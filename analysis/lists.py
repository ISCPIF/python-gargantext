from collections import defaultdict

from gargantext_web.db import session, NodeNgram, NodeNgramNgram, bulk_insert


class BaseClass:

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


class Translations(BaseClass):

    def __init__(self, other=None):
        if other is None:
            self.items = defaultdict(int)
            self.groups = defaultdict(set)
        elif isinstance(other, int):
            query = (session
                .query(NodeNgramNgram.ngramy_id, NodeNgramNgram.ngramx_id)
                .filter(NodeNgramNgram.node_id == other)
            )
            self.items = defaultdict(int, query)
            self.groups = defaultdict(set)
            for key, value in self.items.items():
                self.groups[value].add(key)
        elif isinstance(other, Translations):
            self.items = other.items.copy()
            self.groups = other.groups.copy()
        elif hasattr(other, '__iter__'):
            self.items = defaultdict(int, other)
            self.groups = defaultdict(set)
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

    def save(self, node_id):
        # delete previous data
        session.query(NodeNgramNgram).filter(NodeNgramNgram.node_id == node_id).delete()
        session.commit()
        # insert new data
        bulk_insert(
            NodeNgramNgram,
            ('node_id', 'ngramy_id', 'ngramx_id', 'score'),
            ((node_id, key, value, 1.0) for key, value in self.items.items())
        )


class WeightedMatrix(BaseClass):

    def __init__(self, other=None):
        if other is None:
            self.items = defaultdict(lambda: defaultdict(float))
        elif isinstance(other, WeightedMatrix):
            self.items = other.items.copy()
        elif hasattr(other, '__iter__'):
            self.items = defaultdict(lambda: defaultdict(float))
            for row in other:
                self.items[other[0]][other[1]] = [other[2]]
        else:
            raise TypeError

    def __iter__(self):
        for key1, key2_value in self.items.items():
            for key2, value in key2_value.items():
                yield key1, key2, value

    def __add__(self, other):
        result = NotImplemented
        if isinstance(other, WeightedMatrix):
            result = WeightedMatrix(self)
            for key1, key2_value in other.items.items():
                for key2, value in key2_value.items():
                    result.items[key1][key2] += value
        return result

    def __and__(self, other):
        result = NotImplemented
        if isinstance(other, (UnweightedList, WeightedList)):
            result = WeightedMatrix()
            for key1, key2_value in self.items.items():
                if key1 not in other.items:
                    continue
                for key2, value in key2_value.items():
                    if key2 not in other.items:
                        continue
                    result.items[key1][key2] = value
        return result

    def __rsub__(self, other):
        """Remove elements of the other list from the current one
        Can only be substracted to another list of coocurrences.
        """
        result = NotImplemented
        if isinstance(other, (UnweightedList, WeightedList)):
            result = WeightedMatrix()
            for key1, key2_value in self.items.items():
                if key1 in other.items:
                    continue
                for key2, value in key2_value.items():
                    if key2 in other.items:
                        continue
                    result.items[key1][key2] = value
        return result

    def __mul__(self, other):
        result = NotImplemented
        if isinstance(other, Translations):
            result = WeightedList()
            for key1, key2_value in self.items.items():
                key1 = other.items.get(key1, key1)
                for key2, value in key2_value.items():
                    result.items[key1][
                        other.items.get(key2, key2)
                    ] += value
        return result

    def __iter__(self):
        for key1, key2_value in self.items.items():
            for key2, value in key2_value.items():
                yield key1, key2, value


class UnweightedList(BaseClass):

    def __init__(self, other=None):
        if other is None:
            self.items = set()
        elif isinstance(other, int):
            query = (session
                .query(NodeNgram.ngram_id)
                .filter(NodeNgram.node_id == other)
            )
            self.items = {row[0] for row in query}
        elif isinstance(other, WeightedList):
            self.items = set(other.items.keys())
        elif isinstance(other, UnweightedList):
            self.items = other.items.copy()
        elif hasattr(other, '__iter__'):
            items = tuple(item for item in other)
            if len(items) == 0:
                self.items = set()
            else:
                if hasattr(items[0], '__iter__'):
                    self.items = set(item[0] for item in items)
                else:
                    self.items = set(item for item in items)
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

    def save(self, node_id):
        # delete previous data
        session.query(NodeNgram).filter(NodeNgram.node_id == node_id).delete()
        session.commit()
        # insert new data
        bulk_insert(
            NodeNgram,
            ('node_id', 'ngram_id', 'weight'),
            ((node_id, key, 1.0) for key in self.items)
        )


class WeightedList(BaseClass):

    def __init__(self, other=None):
        if other is None:
            self.items = defaultdict(float)
        elif isinstance(other, int):
            query = (session
                .query(NodeNgram.ngram_id, NodeNgram.weight)
                .filter(NodeNgram.node_id == other)
            )
            self.items = defaultdict(float, query)
        elif isinstance(other, WeightedList):
            self.items = other.items.copy()
        elif isinstance(other, UnweightedList):
            self.items = defaultdict(float)
            for key in other.items:
                self.items[key] = 1.0
        elif hasattr(other, '__iter__'):
            self.items = defaultdict(float, other)
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

    def save(self, node_id):
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
    operands['ul1'] = UnweightedList((1, 2, 3, 4, 5))
    operands['ul2'] = UnweightedList((1, 2, 3, 6))
    # operands['ul2'].save(5)
    # operands['ul3'] = UnweightedList(5)
    operands['wl1'] = WeightedList({1:.7, 2:.8, 7: 1.1})
    # operands['wl1'].save(5)
    # operands['wl2'] = WeightedList(5)
    operands['t1'] = Translations({1:2, 4:5})
    operands['t2'] = Translations({3:2, 4:5})
    # operands['t2'].save(5)
    # operands['t3'] = Translations(5)
    # define operators
    operators = OrderedDict()
    # operators['+'] = '__add__'
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

