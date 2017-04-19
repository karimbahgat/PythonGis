class MissingValue(object):
    """An observation's missing value.

    More information: <http://www.stata.com/help.cgi?missing>""" 

    def __init__(self, offset, value):
        self._value = value
        if type(value) is int or type(value) is long:
            self._str = value-offset is 1 and '.' or ('.' + chr(value-offset+96))
        else:
            self._str = '.'
    string = property(lambda self: self._str, doc="The Stata representation of the missing value: '.', '.a'..'.z'")
    value = property(lambda self: self._value, doc='The binary representation of the missing value.')
    def __str__(self): return self._str
    __str__.__doc__ = string.__doc__

class Variable(object):
    """A dataset variable."""
    def __init__(self, variable_data): self._data = variable_data
    def __int__(self): return self.index
    def __str__(self): return self.name
    index = property(lambda self: self._data[0], doc='the variable\'s index within an observation')
    type = property(lambda self: self._data[1], doc='the data type of variable\n\nPossible types are:\n{1..244:string, b:byte, h:int, l:long, f:float, d:double)')
    name = property(lambda self: self._data[2], doc='the name of the variable')
    format = property(lambda self: self._data[4], doc='the variable\'s Stata format')
    value_format = property(lambda self: self._data[5], doc='the variable\'s value format')
    label = property(lambda self: self._data[6], doc='the variable\'s label')
    __int__.__doc__ = index.__doc__
    __str__.__doc__ = name.__doc__
