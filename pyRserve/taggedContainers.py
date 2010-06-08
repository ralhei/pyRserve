import numpy


class TaggedList(object):
    # This code is mainly based on UserList.UserList and modified for tags
    '''
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
    '''
    def __init__(self, initlist=[]):
        '''
        Items in initlist can either be 
        - tuples of (key,values)
        - or plain values
        Keys can be None or empty strings in item tuples.
        '''
        self.values = []
        self.keys = []
        for idx, item in enumerate(initlist):
            try:
                key, value = item
                key = None if key=='' else key
            except (TypeError, ValueError):
                value = item
                key = None
            finally:
                self.values.append(value)
                self.keys.append(key)
                
    def astuples(self):
        'converts a TaggedList into a representation suitable to be provided to __init__()'
        return zip(self.keys, self.values)
        
    def __repr__(self): 
        data = ["%s=%s" % (key, repr(value)) if key else "'%s'" % value for key,value in self.astuples()]
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
    __hash__ = None # Mutable sequence, so not hashable
    
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
        i = max(i, 0); j = max(j, 0)
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
        i = max(i, 0); j = max(j, 0)
        del self.values[i:j]
        del self.keys[i:j]
        
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
#        return self.__class__(self.values*n)
    __rmul__ = __mul__
    
    def __imul__(self, n):
        raise NotImplementedError()
#        self.values *= n
#        return self
        
    def append(self, *value, **key_and_value):
        if len(value)==1 and not key_and_value:
            key = None
            value = value[0]
        elif len(key_and_value)==1 and not value:
            [(key, value)] = key_and_value.items()
        else:
            raise ValueError("Only either one single value or one single pair of key/value is allowed")
        self.values.append(value)
        self.keys.append(key)
        
    def insert(self, i, *value, **key_and_value):
        if len(value)==1 and not key_and_value:
            key = None
            value = value[0]
        elif len(key_and_value)==1 and not value:
            [(key, value)] = key_and_value.items()
        else:
            raise ValueError("Only either one single value or one single pair of key/value is allowed")
        self.values.insert(i, value)
        self.keys.insert(i, key)
                
    def pop(self, i=-1): 
        return self.values.pop(i)
        return self.keys.pop(i)
        
    def remove(self, item): 
        raise NotImplementedError()
#        self.values.remove(item)
        
    def count(self, item): 
        return self.values.count(item)
    
    def index(self, item, *args): 
        return self.values.index(item, *args)

    def reverse(self): 
        self.values.reverse()
        self.keys.reverse()
    
    def sort(self, *args, **kwds): 
        raise NotImplementedError()
#        self.values.sort(*args, **kwds)
        
    def extend(self, other):
        raise NotImplementedError()
#        if isinstance(other, UserList):
#            self.values.extend(other.data)
#        else:
#            self.values.extend(other)





class AttrArray(numpy.ndarray):
    'numpy.ndarray with additional "attr"-container'
    attr = None
    
    def __repr__(self):
        r = super(AttrArray, self).__repr__()
        if hasattr(self, 'attr'):
            return r[:-1] + ', attr=' + repr(self.attr) + ')'
        return r

def asAttrArray(ndarray, attr):
    arr = ndarray.view(AttrArray)
    arr.attr = attr
    return arr

class TaggedArray(AttrArray):
    attr = []
    def __repr__(self):
        r = super(AttrArray, self).__repr__()
        if hasattr(self, 'attr'):
            return r[:-1] + ', key=' + repr(self.attr) + ')'
        return r

    def __getitem__(self, idx_or_name):
        try:
            return numpy.ndarray.__getitem__(self, idx_or_name)
        except:
            pass
        try:
            return numpy.ndarray.__getitem__(self, self.attr.index(idx_or_name))
        except ValueError:
            raise KeyError('No key "%s" available for array' % idx_or_name)
            
    def keys(self):
        return self.attr[:]

def asTaggedArray(ndarray, tags):
    if len(tags) != len(ndarray):
        raise ValueError('Number of keys must match size of array')
    arr = ndarray.view(TaggedArray)
    arr.attr = tags
    return arr
    
