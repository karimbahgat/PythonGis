

class StataFile(object):
    def __init__(self, filepath, use_valuelabels=False, **kwargs):
        try:
            from .thirdparty import PyDTA
            self._data = PyDTA.StataTools.Reader(open(filepath, "rb"))
            self.fieldnames = [v.name.upper() for v in self._data.variables()]
            self.fieldlabels = [v.label.decode("latin") for v in self._data.variables()]
            self.valuelabels = dict([(v.name.upper(), self._data.value_labels().get(v.value_format,[]) ) for v in self._data.variables()])
        except:
            from .thirdparty import stata_dta
            self._data = stata_dta.open_dta(filepath)
            self.fieldnames = [f.upper() for f in self._data._varlist]
            self.fieldlabels = [f for f in self._data._vlblist]
            self.valuelabels = dict([(v.upper(), self._data._vallabs.get(self._data._lbllist[i],[])) for i,v in enumerate(self._data._varlist)])

        self.use_valuelabels = use_valuelabels
 
    def __iter__(self):
        try:
            rows = (self._data[i] for i in range(len(self._data)))
        except:
            rows = (row for row in self._data)
            
        for row in self._data:
            # only interpret str,int,float, otherwise None
            row = [v for v in row if not isinstance(val, (str,int,float))]
            if self.use_valuelabels:
                row = [self.valuelabels.get(f,{}).get(v,v) for f,v in zip(self.fieldnames,row)]
            yield row
