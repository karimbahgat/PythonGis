
from struct import unpack, calcsize, Struct

from StataTypes import MissingValue, Variable

class Reader(object):
    """.dta file reader"""

    _header = {}
    _data_location = 0
    _col_sizes = ()
    _has_string_data = False
    _missing_values = False
    TYPE_MAP = range(251)+list('bhlfd')
    MISSING_VALUES = { 'b': (-127,100), 'h': (-32767, 32740), 'l': (-2147483647, 2147483620), 'f': (-1.701e+38, +1.701e+38), 'd': (-1.798e+308, +8.988e+307) }

    def __init__(self, file_object, missing_values=False):
        """Creates a new parser from a file object.
        
        If missing_values, parse missing values and return as a MissingValue
        object (instead of None)."""
        self._missing_values = missing_values
        self._parse_header(file_object)

    def file_headers(self):
        """Returns all .dta file headers."""
        return self._header

    def file_format(self):
        """Returns the file format.
        
        Format 113: Stata 9
        Format 114: Stata 10"""
        return self._header['ds_format']

    def file_label(self):
        """Returns the dataset's label."""
        return self._header['data_label']

    def file_timestamp(self):
        """Returns the date and time Stata recorded on last file save."""
        return self._header['time_stamp']

    def value_labels(self):
        return self._header["vallabs"]

    def variables(self):
        """Returns a list of the dataset's PyDTA.Variables."""
        return map(Variable, zip(range(self._header['nvar']),
            self._header['typlist'], self._header['varlist'], self._header['srtlist'],
            self._header['fmtlist'], self._header['lbllist'], self._header['vlblist']))

    def dataset(self, as_dict=False):
        """Returns a Python generator object for iterating over the dataset.
        
        Each observation is returned as a list unless as_dict is set.
        Observations with a MissingValue(s) are not filtered and should be
        handled by your applcation."""
        try:
            self._file.seek(self._data_location)
        except Exception:
            pass

        if as_dict:
            vars = map(str, self.variables())
            for i in range(len(self)):
                yield dict(zip(vars, self._next()))
        else:
            for i in range(self._header['nobs']):
                yield self._next()

    ### Python special methods

    def __len__(self):
        """Return the number of observations in the dataset.

        This value is taken directly from the header and includes observations
        with missing values."""
        return self._header['nobs']

    def __getitem__(self, k):
        """Seek to an observation indexed k in the file and return it, ordered
        by Stata's output to the .dta file.

        k is zero-indexed.  Prefer using R.data() for performance."""
        if not (type(k) is int or type(k) is long) or k < 0 or k > len(self)-1:
            raise IndexError(k)
        loc = self._data_location + sum(self._col_size()) * k
        if self._file.tell() != loc:
            self._file.seek(loc)
        return self._next()

    ### PyDTA private methods

    def _null_terminate(self, s):
        try:
            return s.lstrip('\x00')[:s.index('\x00')]
        except Exception:
            return s

    def _parse_header(self, file_object):
        self._file = file_object

        # parse headers
        self._header['ds_format'] = unpack('b', self._file.read(1))[0]
        byteorder = self._header['byteorder'] = unpack('b', self._file.read(1))[0]==0x1 and '>' or '<'
        self._header['filetype'] = unpack('b', self._file.read(1))[0]
        self._file.read(1)
        nvar = self._header['nvar'] = unpack(byteorder+'h', self._file.read(2))[0]
        if self._header['ds_format'] < 114:
            self._header['nobs'] = unpack(byteorder+'i', self._file.read(4))[0]
        else:
            self._header['nobs'] = unpack(byteorder+'i', self._file.read(4))[0]
        self._header['data_label'] = self._null_terminate(self._file.read(81))
        self._header['time_stamp'] = self._null_terminate(self._file.read(18))

        # parse descriptors
        self._header['typlist'] = [self.TYPE_MAP[ord(self._file.read(1))] for i in range(nvar)]
        self._header['varlist'] = [self._null_terminate(self._file.read(33)) for i in range(nvar)]
        self._header['srtlist'] = unpack(byteorder+('h'*(nvar+1)), self._file.read(2*(nvar+1)))[:-1]
        if self._header['ds_format'] <= 113:
            self._header['fmtlist'] = [self._null_terminate(self._file.read(12)) for i in range(nvar)]
        else:
            self._header['fmtlist'] = [self._null_terminate(self._file.read(49)) for i in range(nvar)]
        self._header['lbllist'] = [self._null_terminate(self._file.read(33)) for i in range(nvar)]
        self._header['vlblist'] = [self._null_terminate(self._file.read(81)) for i in range(nvar)]

        # ignore expansion fields
        while True:
            data_type = unpack(byteorder+'b', self._file.read(1))[0]
            data_len = unpack(byteorder+'i', self._file.read(4))[0]
            if data_type == 0:
                break
            self._file.read(data_len)

        # other state vars
        self._data_location = self._file.tell()
        self._has_string_data = len(filter(lambda x: type(x) is int, self._header['typlist'])) > 0
        self._col_size()

        # create rowunpacker
        typlist = self._header['typlist']
        frmtlist = [t if type(t)!=int else bytes(t)+"s" for t in typlist]
        frmt = "".join(frmtlist)
        frmt = self._header['byteorder'] + frmt
        self._rowstruct = Struct(frmt)

        # offset to value labels
        byteoffset = self._rowstruct.size * self._header["nobs"]
        self._file.seek(byteoffset, 1)

        ###############################
        # value labels
        # taken straight from stata_dta...
        class MissingValue():
            """A class to mimic some of the properties of Stata's missing values.
            
            The class is intended for mimicking only the 27 regular missing
            values ., .a, .b, .c, etc.
            
            Users wanting MissingValue instances should access members of
            MISSING_VALS rather than create new instances.
            
            """
            def __init__(self, index):
                """Users wanting MissingValue instances should access members of
                MISSING_VALS rather than create new instances.
                
                """
                self.value = float.fromhex(
                    "".join(('0x1.0', hex(index)[2:].zfill(2), 'p+1023'))
                )
                self.name = "." if index == 0 else "." + chr(index + 96)
                self.index = index
                    
            def __abs__(self):
                return self
                
            def __add__(self, other):
                return MISSING
                
            def __bool__(self):
                return True
                
            def __divmod__(self, other):
                return MISSING, MISSING
                
            def __eq__(self, other):
                other_val = other.value if isinstance(other, MissingValue) else other
                return self.value == other_val
                
            def __floordiv__(self, other):
                return MISSING
                
            def __ge__(self, other):
                other_val = other.value if isinstance(other, MissingValue) else other
                return self.value >= other_val
                
            def __gt__(self, other):
                other_val = other.value if isinstance(other, MissingValue) else other
                return self.value > other_val
                
            def __hash__(self):
                return self.value.__hash__()
                
            def __le__(self, other):
                other_val = other.value if isinstance(other, MissingValue) else other
                return self.value <= other_val
                
            def __lt__(self, other):
                other_val = other.value if isinstance(other, MissingValue) else other
                return self.value < other_val
                
            def __mod__(self, other):
                return MISSING
                
            def __mul__(self, other):
                return MISSING
                
            def __ne__(self, other):
                other_val = other.value if isinstance(other, MissingValue) else other
                return self.value != other_val
                
            def __neg__(self):
                return MISSING
                
            def __pos__(self):
                return MISSING
                
            def __pow__(self, other):
                return MISSING
                
            def __radd__(self, other):
                return MISSING
                
            def __rdivmod__(self, other):
                return MISSING, MISSING
                
            def __repr__(self):
                return self.name
                
            def __rfloordiv__(self, other):
                return MISSING
                
            def __rmod__(self, other):
                return MISSING
                
            def __rmul__(self, other):
                return MISSING
                
            def __round__(self, ndigits=None):
                return self
                
            def __rpow__(self, other):
                return MISSING
                
            def __rsub__(self, other):
                return MISSING
                
            def __rtruediv__(self, other):
                return MISSING
                
            def __sub__(self, other):
                return MISSING
                
            def __str__(self):
                return self.name
                
            def __truediv__(self, other):
                return MISSING


        MISSING_VALS = tuple(MissingValue(i) for i in range(27))
        
        missing_above = {251: 100, 252: 32740, 253: 2147483620, 
                        254: float.fromhex('0x1.fffffep+126'), 
                        255: float.fromhex('0x1.fffffffffffffp+1022')}
        # decimal numbers given in -help dta- for float and double 
        # are approximations: 'f': 1.701e38, 'd': 8.988e307
        type_dict = {251: ['b',1], 252: ['h',2], 253: ['l',4], 
                    254: ['f',4], 255: ['d',8]}
                    
        def get_byte_str(str_len):
            s = unpack(str(str_len) + 's', self._file.read(str_len))[0]
            return s.partition(b'\0')[0].decode('iso-8859-1')
            
        def missing_object(miss_val, st_type):
            if st_type == 251: # byte
                value = MISSING_VALS[miss_val - 101]
            elif st_type == 252: # int
                value = MISSING_VALS[miss_val - 32741]
            elif st_type == 253: # long
                value = MISSING_VALS[miss_val - 2147483621]
            elif st_type == 254: # float
                value = MISSING_VALS[int(miss_val.hex()[5:7], 16)]
            elif st_type == 255: # double
                value = MISSING_VALS[int(miss_val.hex()[5:7], 16)]
            return value
            
        def get_var_val(st_type):
            if st_type <= 244:
                return get_byte_str(st_type)
            else:
                fmt, nbytes = type_dict[st_type]
                val = unpack(byteorder+fmt, self._file.read(nbytes))[0]
                return (val if val <= missing_above[st_type] 
                        else missing_object(val, st_type))

        def parse_value_label_table():
            """helper function for reading dta files"""
            
            nentries = unpack(byteorder + 'l', self._file.read(4))[0]
            txtlen = unpack(byteorder + 'l', self._file.read(4))[0]
            off = []
            val = []
            txt = []
            for i in range(nentries):
                off.append(unpack(byteorder+'l',self._file.read(4))[0])
            for i in range(nentries):
                val.append(unpack(byteorder+'l',self._file.read(4))[0])
            
            txt_block = unpack(str(txtlen) + "s", self._file.read(txtlen))
            txt = [t.decode('iso-8859-1') 
                   for b in txt_block for t in b.split(b'\0')]
            
            # put (off, val) pairs in same order as txt
            sorter = list(zip(off, val))
            sorter.sort()
            
            # dict of val[i]:txt[i]
            table = {sorter[i][1]: txt[i] for i in range(len(sorter))}
            
            return table
        
        value_labels = {}
        while True:
            try:
                self._file.seek(4,1) # table length
                labname = get_byte_str(33)
                self._file.seek(3,1) # padding
                vl_table = parse_value_label_table()
                value_labels[labname] = vl_table
            except:
                break
        self._header['vallabs'] = value_labels
        

    def _calcsize(self, fmt):
        return type(fmt) is int and fmt or calcsize(self._header['byteorder']+fmt)

    def _col_size(self, k = None):
        """Calculate size of a data record."""
        if len(self._col_sizes) == 0:
            self._col_sizes = map(lambda x: self._calcsize(x), self._header['typlist'])
        if k == None:
            return self._col_sizes
        else:
            return self._col_sizes[k]

    def _unpack(self, fmt, byt):
        d = unpack(self._header['byteorder']+fmt, byt)[0]
        if fmt[-1] in self.MISSING_VALUES:
            nmin, nmax = self.MISSING_VALUES[fmt[-1]]
            if d < nmin or d > nmax:
                if self._missing_values:
                    return MissingValue(nmax, d)
                else:
                    return None
        return d

    def _next(self):
        # what about nullterminate on strings?
        row = self._rowstruct.unpack(self._file.read(self._rowstruct.size))

        # turn missing values into MissingValue or None
        # TODO: This step alone can increase speed from 1 sec to 26 sec.
        # so possible with some optimization...
        typlist = self._header["typlist"]
        valtyps = zip(row,typlist)
        def missingfilter():
            if self._missing_values:
                for val,typ in valtyps:
                    if typ in self.MISSING_VALUES:
                        nmin, nmax = self.MISSING_VALUES[typ]
                        if not nmin <= val <= nmax:
                            yield MissingValue(nmax, val) # only difference
                        else:
                            yield val
                    else:
                        yield val
            else:
                for val,typ in valtyps:
                    if typ in self.MISSING_VALUES:
                        nmin, nmax = self.MISSING_VALUES[typ]
                        if not nmin <= val <= nmax:
                            yield None # only difference
                        else:
                            yield val
                    else:
                        yield val
        row = list(missingfilter())
        
        return row
        
##        if self._has_string_data:
##            data = [None]*self._header['nvar']
##            for i in range(len(data)):
##                if type(typlist[i]) is int:
##                    data[i] = self._null_terminate(self._file.read(typlist[i]))
##                else:
##                    data[i] = self._unpack(typlist[i], self._file.read(self._col_size(i)))
##            return data
##        else:
##            return map(lambda i: self._unpack(typlist[i], self._file.read(self._col_size(i))), range(self._header['nvar']))
