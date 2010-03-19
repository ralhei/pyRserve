import numpy


class TaggedList(object):
    # This code is mainly based on UserList.UserList and modified for tags
    def __init__(self, initlist=[]):
        self.values = []
        self.keys = []
        # Items in initlist can either be 
        # - tuples of (key,values)
        # - or plain values
        # Keys can be None of empty strings in item tuples.
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
                
    @property
    def astuples(self):
        'converts a TaggedList into a representation suitable to be provided to __init__()'
        return zip(self.keys, self.values)
        
    def __repr__(self): 
        data = ["%s='%s'" % (key, value) if key else "'%s'" % value for key,value in self.astuples]
        return '<TaggedList(%s)>' % ', '.join(data)
        return repr(self.astuples)

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
        return self.__class__(self.astuples[i:j])
        
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
    'numpy.ndarray with additional "attr"-attribute'
    attr = None
    
def asAttrArray(ndarray, attr):
    arr = ndarray.view(AttrArray)
    arr.attr = attr
    return attr
    
class TaggedArray(AttrArray):
    attr = []
    def __getitem__(self, idx_or_name):
        try:
            return numpy.ndarray.__getitem__(self, idx_or_name)
        except:
            pass
        try:
            return numpy.ndarray.__getitem__(self, self.attr.index(idx_or_name))
        except ValueError:
            raise KeyError('No tag "%s" available for array' % idx_or_name)
            
    def keys(self):
        return self.attr[:]

def asTaggedArray(ndarray, tags):
    if len(tags) != len(ndarray):
        raise ValueError('Number of tags must match size of array')
    arr = ndarray.view(TaggedArray)
    arr.attr = tags
    return arr
    
