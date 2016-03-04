"""Allows easier lists management (synonyms, blacklists, whitelists, etc.)
"""


__all__ = ['Translations', 'WeightedMatrix', 'UnweightedList', 'WeightedList']


from gargantext.util.db import session, bulk_insert

from collections import defaultdict
from math import sqrt



class _BaseClass:

    def __add__(self, other):
        if hasattr(self, '__radd__'):
            return self.__radd__(other)
        else:
            return NotImplemented

    def __sub__(self, other):
        if hasattr(self, '__rsub__'):
            return self.__rsub__(other)
        else:
            return NotImplemented

    def __mul__(self, other):
        if hasattr(self, '__rmul__'):
            return self.__rmul__(other)
        else:
            return NotImplemented

    def __div__(self, other):
        if hasattr(self, '__rdiv__'):
            return self.__rdiv__(other)
        else:
            return NotImplemented

    def __and__(self, other):
        if hasattr(self, '__rand__'):
            return self.__rand__(other)
        else:
            return NotImplemented

    def __or__(self, other):
        if hasattr(self, '__ror__'):
            return self.__ror__(other)
        else:
            return NotImplemented

    def __repr__(self):
        items = self.items
        if isinstance(items, defaultdict):
            if len(items) and isinstance(next(iter(items.values())), defaultdict):
                items = {
                    key: dict(value)
                    for key, value in items.items()
                }
            else:
                items = dict(items)
        return '<%s %s>' % (
             self.__class__.__name__,
             repr(items),
        )

    __str__ = __repr__


class Translations(_BaseClass):

    def __init__(self, source=None, just_items=False):
        self.items = defaultdict(int)
        # TODO lazyinit for groups
        #      (not necessary for save)
        self.groups = defaultdict(set)
        if source is None:
            return
        elif isinstance(source, int):
            self.id = source
            from gargantext.models import NodeNgramNgram
            query = (session
                .query(NodeNgramNgram.ngram2_id, NodeNgramNgram.ngram1_id)
                .filter(NodeNgramNgram.node_id == source)
            )
            self.items.update(query)
            if not just_items:
                for key, value in self.items.items():
                    self.groups[value].add(key)
        elif isinstance(source, Translations):
            self.items.update(source.items)
            if not just_items:
                self.groups.update(source.groups)
        elif hasattr(source, '__iter__'):
            # not very intuitive with update here:
            # /!\ source must be "reversed" (like self.items)

            # bad exemple
            # In > couples = [(1, 2), (1, 3)]
            # In > tlko = Translations(couples)
            # Out> Translations {1: 3}
            # In > tlko.save()
            # DB-- 3 -> 1

            # good exemple
            # In > reversed_couples = [(2, 1), (3, 1)]
            # In > tlok = Translations(reversed_couples)
            # Out> Translations {2: 1, 3: 1}
            # In > tlok.save()
            # DB-- 1 -> 2
            # DB-- 1 -> 3
            self.items.update(source)
            if not just_items:
                for key, value in self.items.items():
                    self.groups[value].add(key)
        else:
            raise TypeError

    def __rmul__(self, other):
        result = NotImplemented
        if isinstance(other, UnweightedList):
            result = UnweightedList()
            result.items = set(
                self.items.get(key, key)
                for key in other.items
            )
        elif isinstance(other, WeightedList):
            result = WeightedList()
            for key, value in other.items.items():
                result.items[
                    self.items.get(key, key)
                ] += value
        elif isinstance(other, Translations):
            result = Translations()
            items = self.items
            items.update(other.items)
            for key, value in items.items():
                if value in items:
                    value = items[value]
                if key != value:
                    result.items[key] = value
                    result.groups[value].add(key)
        return result

    def __iter__(self):
        for key, value in self.items.items():
            yield key, value

    def save(self, node_id=None):
        from gargantext.models import NodeNgramNgram
        if node_id is None:
            if hasattr(self, 'id'):
                node_id = self.id
            else:
                raise ValueError('Please mention an ID to save the node.')
        # delete previous data
        session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id == node_id).delete()
        session.commit()
        # insert new data
        bulk_insert(
            NodeNgramNgram,
            ('node_id', 'ngram2_id', 'ngram1_id', 'weight'),
            ((node_id, key, value, 1.0) for key, value in self.items.items())
        )


class WeightedMatrix(_BaseClass):

    def __init__(self, source=None):
        self.items = defaultdict(float)
        if source is None:
            return
        elif isinstance(source, int):
            self.id = source
            from gargantext.models import NodeNgramNgram
            query = (session
                .query(NodeNgramNgram.ngram1_id, NodeNgramNgram.ngram2_id, NodeNgramNgram.score)
                .filter(NodeNgramNgram.node_id == source)
            )
            for key1, key2, value in self.items.items():
                self.items[key1, key2] = value
        elif isinstance(source, WeightedMatrix):
            for key1, key2, value in source:
                self.items[key1, key2] = value
        elif hasattr(source, '__iter__'):
            for row in source:
                self.items[row[0], row[1]] = row[2]
        else:
            raise TypeError

    def __iter__(self):
        for (key1, key2), value in self.items.items():
            yield key1, key2, value

    def save(self, node_id=None):
        from gargantext.models import NodeNgramNgram
        if node_id is None:
            if hasattr(self, 'id'):
                node_id = self.id
            else:
                raise ValueError('Please mention an ID to save the node.')
        # delete previous data
        session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id == node_id).delete()
        session.commit()
        # insert new data
        bulk_insert(
            NodeNgramNgram,
            ('node_id', 'ngram1_id', 'ngram2_id', 'score'),
            ((node_id, key1, key2, value) for key1, key2, value in self)
        )

    def __radd__(self, other):
        result = NotImplemented
        if isinstance(other, WeightedMatrix):
            result = WeightedMatrix()
            for key1, key2, value in self:
                value = value + other.items[key1, key2]
                if value != 0.0:
                    result.items[key1, key2] = value
        return result

    def __rsub__(self, other):
        result = NotImplemented
        if isinstance(other, (UnweightedList, WeightedList)):
            result = WeightedMatrix()
            for key1, key2, value in self:
                if key1 in other.items or key2 in other.items:
                    continue
                result.items[key1, key2] = value
        elif isinstance(other, WeightedMatrix):
            result = WeightedMatrix()
            for key1, key2, value in self:
                value = value - other.items[key1, key2]
                if value != 0.0:
                    result.items[key1, key2] = value
        return result

    def __rand__(self, other):
        result = NotImplemented
        if isinstance(other, (UnweightedList, WeightedList)):
            result = WeightedMatrix()
            for key1, key2, value in self:
                if key1 not in other.items or key2 not in other.items:
                    continue
                result.items[key1, key2] = value
        return result

    def __rmul__(self, other):
        result = NotImplemented
        if isinstance(other, Translations):
            result = WeightedMatrix()
            for (key1, key2), value in self.items.items():
                result.items[key1,
                    other.items.get(key2, key2)
                ] += value
        elif isinstance(other, UnweightedList):
            result = self.__rand__(other)
        # elif isinstance(other, WeightedMatrix):
        #     result = WeightedMatrix()
        elif isinstance(other, WeightedList):
            result = WeightedMatrix()
            for key1, key2, value in self:
                if key1 not in other.items or key2 not in other.items:
                    continue
                result.items[key1, key2] = value * sqrt(other.items[key1] * other.items[key2])
        return result

    def __rdiv__(self, other):
        result = NotImplemented
        if isinstance(other, WeightedList):
            result = WeightedMatrix()
            for key1, key2, value in self:
                if key1 not in other.items or key2 not in other.items:
                    continue
                result.items[key1, key2] = value / sqrt(other.items[key1] * other.items[key2])
        return result


class UnweightedList(_BaseClass):

    def __init__(self, source=None):
        self.items = set()
        if source is None:
            return
        elif isinstance(source, int):
            self.id = source
            from gargantext.models import NodeNgram
            query = (session
                .query(NodeNgram.ngram_id)
                .filter(NodeNgram.node_id == source)
            )
            self.items.update(row[0] for row in query)
        elif isinstance(source, WeightedList):
            self.items.update(source.items.keys())
        elif isinstance(source, UnweightedList):
            self.items.update(source.items)
        elif hasattr(source, '__iter__'):
            items = tuple(item for item in source)
            if len(items) == 0:
                return
            if hasattr(items[0], '__iter__'):
                self.items.update(item[0] for item in items)
            else:
                self.items.update(items)
        else:
            raise TypeError

    def __radd__(self, other):
        result = NotImplemented
        if isinstance(other, UnweightedList):
            result = UnweightedList(other)
            result.items |= self.items
        elif isinstance(other, WeightedList):
            result = WeightedList(other)
            for key in self.items:
                result.items[key] += 1.0
        return result

    def __rsub__(self, other):
        result = NotImplemented
        if isinstance(other, UnweightedList):
            result = UnweightedList(self)
            result.items -= other.items
        elif isinstance(other, WeightedList):
            result = UnweightedList(self)
            result.items -= set(other.items.keys())
        return result

    def __ror__(self, other):
        result = NotImplemented
        if isinstance(other, UnweightedList):
            result = UnweightedList(self)
            result.items |= other.items
        elif isinstance(other, WeightedList):
            result = UnweightedList(self)
            result.items |= set(other.items.keys())
        return result

    def __rand__(self, other):
        result = NotImplemented
        if isinstance(other, UnweightedList):
            result = UnweightedList(self)
            result.items &= other.items
        elif isinstance(other, WeightedList):
            result = UnweightedList(self)
            result.items &= set(other.items)
        return result

    def __rmul__(self, other):
        result = NotImplemented
        if isinstance(other, Translations):
            result = UnweightedList()
            result.items = set(
                other.items.get(key, key)
                for key in self.items
            )
        elif isinstance(other, UnweightedList):
            result = WeightedList(self)
            result.items = {key: 1.0 for key in self.items & other.items}
        elif isinstance(other, WeightedList):
            result = WeightedList()
            result.items = {key: value for key, value in other.items.items() if key in self.items}
        return result

    def save(self, node_id=None):
        from gargantext.models import NodeNgram
        if node_id is None:
            if hasattr(self, 'id'):
                node_id = self.id
            else:
                raise ValueError('Please mention an ID to save the node.')
        # delete previous data
        session.query(NodeNgram).filter(NodeNgram.node_id == node_id).delete()
        session.commit()
        # insert new data
        bulk_insert(
            NodeNgram,
            ('node_id', 'ngram_id', 'weight'),
            ((node_id, key, 1.0) for key in self.items)
        )


class WeightedList(_BaseClass):

    def __init__(self, source=None):
        self.items = defaultdict(float)
        if source is None:
            return
        elif isinstance(source, int):
            self.id = source
            from gargantext.models import NodeNgram
            query = (session
                .query(NodeNgram.ngram_id, NodeNgram.weight)
                .filter(NodeNgram.node_id == source)
            )
            self.items.update(query)
        elif isinstance(source, WeightedList):
            self.items = source.items.copy()
        elif isinstance(source, UnweightedList):
            for key in source.items:
                self.items[key] = 1.0
        elif hasattr(source, '__iter__'):
            self.items.update(source)
        else:
            raise TypeError

    def __iter__(self):
        for key, value in self.items.items():
            yield key, value

    def __radd__(self, other):
        result = NotImplemented
        if isinstance(other, WeightedList):
            result = WeightedList(self)
            for key, value in other.items.items():
                result.items[key] += value
        elif isinstance(other, UnweightedList):
            result = WeightedList(self)
            for key in other.items:
                result.items[key] += 1.0
        return result

    def __rsub__(self, other):
        """Remove elements of the other list from the current one
        """
        result = NotImplemented
        if isinstance(other, UnweightedList):
            result = WeightedList()
            result.items = {key: value for key, value in self.items.items() if key not in other.items}
        elif isinstance(other, WeightedList):
            result = WeightedList(self)
            for key, value in other.items.items():
                if key in result.items and result.items[key] == value:
                    result.items.pop(key)
                else:
                    result.items[key] -= value
        return result

    def __ror__(self, other):
        result = NotImplemented
        if isinstance(other, UnweightedList):
            result = UnweightedList(self)
            result.items |= other.items
        elif isinstance(other, WeightedList):
            result = UnweightedList(self)
            result.items |= set(other.items.keys())
        return result

    def __rmul__(self, other):
        result = NotImplemented
        if isinstance(other, WeightedList):
            result = WeightedList()
            result.items = {
                key: value * other.items[key]
                for key, value
                in self.items.items()
                if key in other.items
            }
        if isinstance(other, UnweightedList):
            result = WeightedList()
            result.items = {
                key: value
                for key, value
                in self.items.items()
                if key in other.items
            }
        elif isinstance(other, Translations):
            result = WeightedList()
            for key, value in self.items.items():
                result.items[
                    other.items.get(key, key)
                ] += value
        return result

    def __rand__(self, other):
        result = NotImplemented
        if isinstance(other, UnweightedList):
            result = UnweightedList(self)
            result.items &= other.items
        elif isinstance(other, WeightedList):
            result = UnweightedList(self)
            result.items &= set(other.items.keys())
        return result

    def save(self, node_id=None):
        from gargantext.models import NodeNgram
        if node_id is None:
            if hasattr(self, 'id'):
                node_id = self.id
            else:
                raise ValueError('Please mention an ID to save the node.')
        # delete previous data
        session.query(NodeNgram).filter(NodeNgram.node_id == node_id).delete()
        session.commit()
        # insert new data
        bulk_insert(
            NodeNgram,
            ('node_id', 'ngram_id', 'weight'),
            ((node_id, key, value) for key, value in self.items.items())
        )


def test():
    from collections import OrderedDict
    # define operands
    operands = OrderedDict()
    operands['wm'] = WeightedMatrix(((1, 2, .5), (1, 3, .75), (2, 3, .6), (3, 3, 1), ))
    operands['ul'] = UnweightedList((1, 2, 3, 4, 5))
    # operands['ul'] = UnweightedList(82986)
    # operands['ul2'] = UnweightedList((1, 2, 3, 6))
    # operands['ul2'].save(5)
    # operands['ul3'] = UnweightedList(5)
    operands['wl'] = WeightedList({1:.7, 2:.8, 7: 1.1})
    # operands['wl1'].save(5)
    # operands['wl2'] = WeightedList(5)
    # operands['t1'] = Translations({1:2, 4:5})
    operands['t'] = Translations({3:2, 4:5})
    # operands['t2'].save(5)
    # operands['t3'] = Translations(5)
    # define operators
    operators = OrderedDict()
    operators['+'] = '__add__'
    operators['-'] = '__sub__'
    operators['*'] = '__mul__'
    operators['|'] = '__or__'
    operators['&'] = '__and__'
    # show operands
    for operand_name, operand in operands.items():
        print('%4s = %s' % (operand_name, operand))
    # show operations results
    for operator_name, operator in operators.items():
        print()
        for operand1_name, operand1 in operands.items():
            for operand2_name, operand2 in operands.items():
                if hasattr(operand1, operator):
                    result = getattr(operand1, operator)(operand2)
                else:
                    result = '?'
                print('%4s %s %-4s =  %s' % (
                    operand1_name,
                    operator_name,
                    operand2_name,
                    '?' if result == NotImplemented else result,
                ))


if __name__ == '__main__':
    test()
