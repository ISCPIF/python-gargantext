from collections import defaultdict


class Translations:

    def __init__(self, other=None):
        if other is None:
            self.items = defaultdict(int)
            self.groups = defaultdict(set)
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

    def __add__(self, other):
        result = self.__class__(self)
        result.items.update(other)
        for key, value in other.groups:
            result.groups[key] += value
        return result

    def __sub__(self, other):
        result = self.__class__(self)
        if isinstance(other, Translations):
            for key, value in other.items.items():
                result.items.pop(key, None)
                result.groups[value].remove(key)
                if len(result.groups[value]) == 0:
                    result.groups.pop(value)
        return result

    def __iter__(self):
        for key, value in self.items.items():
            yield key, value


class WeightedMatrix:

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

    def __sub__(self, other):
        """Remove elements of the other list from the current one
        Can only be substracted to another list of coocurrences.
        """
        pass

   def __mul__(self, other):
    if isinstance(other, Translations):
        result = WeightedMatrix()
        for key1, key2_value in self.items.items():
            for key2, value in self.items:
                result.items[
                    other.items.get(key, key)
                ] = value
    else:
        raise TypeError
    return result


class UnweightedList:

    def __init__(self, other=None):
        if other is None:
            self.items = set()
        elif isinstance(other, WeightedList):
            self.items = set(other.items.keys())
        elif isinstance(other, UnweightedList):
            self.items = other.items.copy()
        elif hasattr(other, '__iter__'):
            items = (item for item in other)
            if len(items) == 0:
                self.items = set()
            else:
                if hasattr(items[0], '__iter__'):
                    self.items = set(item[0] for item in items)
                else:
                    self.items = set(item for item in items)
        else:
            raise TypeError

    def __add__(self, other):
        result = self.__class__(self)
        if isinstance(other, UnweightedList):
            result.items |= other.items
        elif isinstance(other, WeightedList):
            result.items |= set(other.items.keys())
        else:
            raise TypeError
        return result

    __or__ = __add__

    def __sub__(self, other):
        result = self.__class__(self)
        if isinstance(other, UnweightedList):
            result.items -= other.items
        elif isinstance(other, WeightedList):
            result.items -= set(other.items.keys())
        else:
            raise TypeError
        return result

    def __and__(self, other):
        result = self.__class__(self)
        if isinstance(other, UnweightedList):
            result.items &= other.items
        elif isinstance(other, WeightedList):
            result.items &= set(other.items.keys())
        else:
            raise TypeError
        return result


class WeightedList:

    def __init__(self, other=None):
        if other is None:
            self.items = defaultdict(float)
        elif isinstance(other, WeightedList):
            self.items = other.items.copy()
        elif isinstance(other, UnweightedList):
            self.items = defaultdict(float)
            for key in other.items:
                self.items[key] = 1.0
        elif hasattr(other, '__iter__'):
            self.items = defaultdict(float, items)
        else:
            raise TypeError

    def __iter__(self):
        for key, value in self.items.items():
            yield key, value

    def __add__(self, other):
        """Add elements from the other list to the current one
        """
        result = self.__class__(self)
        if isinstance(other, UnweightedList):
            for key, value in other.items:
                result.items[key] += 1.0
        elif isinstance(other, WeightedList):
            for key, value in other.items:
                result.items[key] += value
        else:
            raise TypeError
        return result

    def __sub__(self, other):
        """Remove elements of the other list from the current one
        """
        result = self.__class__(self)
        if isinstance(other, UnweightedList):
            for key in other.items:
                result.items.pop(key, None)
        else:
            raise TypeError
        return result

    def __and__(self, other):
        if isinstance(other, UnweightedList):
            result = defaultdict(float)
            for key, value in self.items.items():
                if item in other.items:
                    result[key] = value
        else:
            raise TypeError
        return result

    def __mul__(self, other):
        if isinstance(other, Translations):
            result = WeightedList()
            for key, value in self.items:
                result.items[
                    other.items.get(key, key)
                ] += value
        else:
            raise TypeError
        return result


# if __name__ == '__main__':
    # l = Coocurrences()
    # l = List()
    # for i in l:
    #     print(i)
    # t1 = Translations()
    # t2 = Translations()
    # t2.items = {1: 2}
    # for i in t1 + t2:
    #     print(i)
