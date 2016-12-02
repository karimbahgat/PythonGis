
from shapely.geometry import shape

class Shapely(object):
    def __init__(self, obj):
        # stored internally as shapely
        if isinstance(obj, dict):
            self._data = shape(obj)
        elif "shapely" in type(obj):
            self._data = obj
        elif isinstance(obj, Shapely):
            self._data = obj._data
        else:
            raise Exception()

    def __getattr__(self, attr):
        # acceses all shapely methods directly
        return getattr(self._data, attr)
