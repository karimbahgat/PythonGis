
# various spatial indexes


# main interface

# MAYBE DROP Spindex CLASS, INSTEAD JUST DIRECTLY USE THE SPECIFIC TYPE INDEX CLASS? 

class Spindex(object):
    
    def __init__(self, type=None, **kwargs):
        type = type.lower() if type else type

        # set default
        if not type:
            type = 'rtree'

        # create specified index
        if type == 'rtree':
            try:
                self._index = Rtree(**kwargs)
            except:
                self._index = PyrTree(**kwargs)

        elif type == 'quadtree':
            self._index = PyqTree(**kwargs)

    def insert(self, id, bbox):
        self._index.insert(id, bbox)

    def intersection(self, bbox):
        return self._index.intersection(bbox)

    def disjoint(self, bbox):
        raise NotImplemented()

    def nearest(self, bbox, **kwargs):
        return self._index.nearest(bbox, **kwargs)


# specific index interfaces

class Rtree(object):

    def __init__(self, **kwargs):
        import rtree
        self._backend = rtree.index.Index(**kwargs)

    def insert(self, id, bbox):
        self._backend.insert(id, bbox)

    def intersection(self, bbox):
        return self._backend.intersection(bbox)

    def nearest(self, bbox, **kwargs):
        return self._backend.nearest(bbox, **kwargs)

class PyrTree(object):

    def __init__(self, **kwargs):
        import pyrtree
        self._backend = pyrtree.RTree(**kwargs)
        self._new_rect = pyrtree.Rect

    def insert(self, id, bbox):
        rect = self._new_rect(*bbox)
        self._backend.insert(id, rect)

    def intersection(self, bbox):
        rect = self._new_rect(*bbox)
        
        res = (node.leaf_obj() for node in self._backend.query_rect(rect)
               if node.is_leaf())
        return res

    def nearest(self, bbox, **kwargs):
        raise NotImplemented()

class PyqTree(object):

    def __init__(self, **kwargs):
        import pyqtree
        self._backend = pyqtree.Index(**kwargs)

    def insert(self, id, bbox):
        self._backend.insert(id, bbox)

    def intersection(self, bbox):
        return self._backend.intersect(bbox)

    def nearest(self, bbox, **kwargs):
        raise NotImplemented



