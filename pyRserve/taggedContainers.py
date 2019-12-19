"""
Some specialized list and array classes to store results obtained from R. These
classes provide means not to only access object items by index but also - sort
of like a dictionary - by key. However keys must not be unique or can even be
None. In those cases only the first item with that key is found.

Available classes:
- TaggedList
- TaggedArray
"""
import numpy


class TaggedList(object):
    # This code is mainly based on UserList.UserList and modified for tags
    """
    A tagged list is useful for additionally addressing individual items by
    name instead of only by index. In contrast to dictionaries multiple items
    can have the same name or key. However only the first one will be found.

    In many cases a TaggedList behaves like a normal list, however for lazyness
    reasons of the programmer not all methods are implemented yet.

    Example:
    l = TaggedList( [('v1', 1), ('v2', 2), 3, ('v2', 4)] )
    l[0]     # returns 1
    l['v1']  # returns 1
    l['v2']  # returns 2  (not 4 !)
    l[3]     # returns 4

    Data can be appended or inserted in the following way:
    l.insert(0, x=3)
    l['x']   # returns 3
    l[0]     # also returns 3

    l.append(y=3)
    l[-1]    # returns 3
    """
    def __init__(self, initlist=()):
        """
        Items in initlist can either be
        - tuples of (key,values)
        - or plain values
        Keys can be None or empty strings in item tuples.
        """
        self.values = []
        self.keys = []
        for idx, item in enumerate(initlist):
            try:
                key, value = item
                key = None if key == '' else key
            except (TypeError, ValueError):
                value = item
                key = None

            self.values.append(value)
            self.keys.append(key)

    def astuples(self):
        """
        Convert a TaggedList into a representation suitable to be provided
        to __init__()
        """
        return list(zip(self.keys, self.values))

    def __repr__(self):
        data = ["%s=%s" % (key, repr(value)) if key else "'%s'" % value
                for key, value in self.astuples()]
        return '<TaggedList(%s)>' % ', '.join(data)

    #    def __lt__(self, other): return self.values <  self.__cast(other)
    #    def __le__(self, other): return self.values <= self.__cast(other)
    #    def __eq__(self, other): return self.values == self.__cast(other)
    #    def __ne__(self, other): return self.values != self.__cast(other)
    #    def __gt__(self, other): return self.values >  self.__cast(other)
    #    def __ge__(self, other): return self.values >= self.__cast(other)
    #    def __cast(self, other):
    #        if isinstance(other, UserList): return other.data
    #        else: return other
    #    def __cmp__(self, other):
    #        return cmp(self.values, self.__cast(other))
    __hash__ = None  # Mutable sequence, so not hashable

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.__dict__ == other.__dict__

    def __ne__(self, other):
        return not self.__eq__(other)

    def __contains__(self, item):
        return item in self.values

    def __len__(self):
        return len(self.values)

    def __getitem__(self, i):
        if type(i) == str:
            i = self.keys.index(i)
        return self.values[i]

    def __setitem__(self, i, item):
        if type(i) == str:
            i = self.keys.index[i]
        self.values[i] = item

    def __delitem__(self, i):
        if type(i) == str:
            i = self.keys.index[i]
            del self.keys[i]
        del self.values[i]

    def __getslice__(self, i, j):
        i = max(i, 0)
        j = max(j, 0)
        return self.__class__(self.astuples()[i:j])

    #    def __setslice__(self, i, j, other):
    #        i = max(i, 0); j = max(j, 0)
    #        if isinstance(other, UserList):
    #            self.values[i:j] = other.data
    #        elif isinstance(other, type(self.values)):
    #            self.values[i:j] = other
    #        else:
    #            self.values[i:j] = list(other)

    def __delslice__(self, i, j):
        raise NotImplementedError()
        # i = max(i, 0); j = max(j, 0)
        # del self.values[i:j]
        # del self.keys[i:j]

    def __add__(self, other):
        raise NotImplementedError()
        #        if isinstance(other, UserList):
        #            return self.__class__(self.values + other.data)
        #        elif isinstance(other, type(self.values)):
        #            return self.__class__(self.values + other)
        #        else:
        #            return self.__class__(self.values + list(other))

    def __radd__(self, other):
        raise NotImplementedError()
        #        if isinstance(other, UserList):
        #            return self.__class__(other.data + self.values)
        #        elif isinstance(other, type(self.values)):
        #            return self.__class__(other + self.values)
        #            return self.__class__(list(other) + self.values)

    def __iadd__(self, other):
        raise NotImplementedError()
        #        if isinstance(other, UserList):
        #            self.values += other.data
        #        elif isinstance(other, type(self.values)):
        #            self.values += other
        #        else:
        #            self.values += list(other)
        #        return self

    def __mul__(self, n):
        raise NotImplementedError()
        # return self.__class__(self.values*n)
    __rmul__ = __mul__

    def __imul__(self, n):
        raise NotImplementedError()
        # self.values *= n
        # return self

    def append(self, *value, **key_and_value):
        """
        Append an item to the list, either given as plain value or as a
        keyword-arg pair.
        Example:
            taggedlist.append(4)
        or
            taggedlist.append(k=4)
        """
        if len(value) == 1 and not key_and_value:
            key = None
            value = value[0]
        elif len(key_and_value) == 1 and not value:
            [(key, value)] = key_and_value.items()
        else:
            raise ValueError("Only either one single value or one single pair "
                             "of key/value is allowed")
        self.values.append(value)
        self.keys.append(key)

    def insert(self, i, *value, **key_and_value):
        """
        Insert an item in the list at position i, either given as plain value
        or as a keyword-arg pair.
        Example:
            taggedlist.insert(4, 'abc)
        or
            taggedlist.append(4, k='abc')
        """
        if len(value) == 1 and not key_and_value:
            key = None
            value = value[0]
        elif len(key_and_value) == 1 and not value:
            [(key, value)] = key_and_value.items()
        else:
            raise ValueError("Only either one single value or one single pair "
                             "of key/value is allowed")
        self.values.insert(i, value)
        self.keys.insert(i, key)

    def pop(self, i=-1):
        """
        Remove an item from the list. By default the last item will be removed.
        If an item at a specific position should be removed, pass an additional
        index arguemnt.
        """
        return self.values.pop(i)

    def remove(self, item):
        raise NotImplementedError()
        # self.values.remove(item)

    def count(self, item):
        return self.values.count(item)

    def index(self, item, *args):
        return self.values.index(item, *args)

    def reverse(self):
        self.values.reverse()
        self.keys.reverse()

    def sort(self, *args, **kwds):
        raise NotImplementedError()
        # self.values.sort(*args, **kwds)

    def extend(self, other):
        raise NotImplementedError()
        #  if isinstance(other, UserList):
        #      self.values.extend(other.data)
        #  else:
        #      self.values.extend(other)


class AttrArray(numpy.ndarray):
    """
    numpy.ndarray with additional "attr"-container.
    Used as base class for TaggedArray.
    """
    attr = None

    def __repr__(self):
        r = super(AttrArray, self).__repr__()
        if hasattr(self, 'attr'):
            return r[:-1] + ', attr=' + repr(self.attr) + ')'
        return r

    @classmethod
    def new(cls, data, attr):
        """
        Factory method to create AttrArray objects from ndarrays or Python
        lists.
        Usage:
            AttrArray.new(array([1, 2, 3, 4]), {'attr1': val1, 'attr2': val2})
        """
        if not isinstance(data, numpy.ndarray):
            # assume it is a Python list or any other valid data type
            # for arrays
            arr = numpy.array(data)
        else:
            arr = data

        attrArr = arr.view(cls)
        attrArr.attr = attr
        return attrArr


def asAttrArray(data, attr):
    return AttrArray.new(data, attr)


class TaggedArray(AttrArray):
    """
    A tagged array is useful for additionally addressing individual items by
    name instead of only by index. In contrast to dictionaries multiple items
    can have the same name or key. However only the first one will be found.

    In many cases a TaggedArray behaves like a normal array and is the
    equivalent for TaggedList.
    This class is basically only useful to translate results created by R into
    something useful in Python.

    Instances of TaggedArray should only be created using the factory function
    'asTaggedArray([values)], [tags])', where 'values' and 'tags' can be plain
    python lists or numpy-arrays.

    Example:
    l = asTaggedArray(array([1, 2, 3, 4]), ['v1', 'v2', 'v3', 'v4'])
    l[0]     # returns 1
    l['v1']  # returns 1
    l['v2']  # returns 2  (not 4 !)
    l[3]     # returns 4

    It is recommended not to do lots of manipulations that modify the
    structure of the arrary. This could lead to mismatched btw. tags and
    values (those are only very loosely coupled internally). However any type
    of mathematics like multiplying the array should be possible without
    problems.
    """
    attr = []

    def __repr__(self):
        r = super(AttrArray, self).__repr__()
        if hasattr(self, 'attr'):
            return r[:-1] + ', key=' + repr(self.attr) + ')'
        return r

    def __getitem__(self, idx_or_name):
        try:
            return numpy.ndarray.__getitem__(self, idx_or_name)
        except Exception:
            pass
        try:
            return numpy.ndarray.__getitem__(self,
                                             self.attr.index(idx_or_name))
        except ValueError:
            raise KeyError('No key "%s" available for array' % idx_or_name)

    def keys(self):
        return self.attr[:]

    @classmethod
    def new(cls, data, tags):
        """
        Factory method to create TaggedArray objects from ndarrays or Python
        lists.
        Check the docs in TaggedArray for more information.
        Usage:
        l = TaggedArray.new(array([1, 2, 3, 4]), ['v1', 'v2', 'v3', 'v4'])
        l[0]     # returns 1
        l['v1']  # returns 1
        l['v2']  # returns 2  (not 4 !)
        l[3]     # returns 4
        """
        if len(tags) != len(data):
            raise ValueError('Number of keys must match size of array')
        if not isinstance(data, numpy.ndarray):
            # assume it is a Python list or any other valid data type
            # for arrays
            arr = numpy.array(data)
        else:
            arr = data

        taggedArr = arr.view(cls)
        taggedArr.attr = tags
        return taggedArr


def asTaggedArray(data, tags):
    return TaggedArray.new(data, tags)
