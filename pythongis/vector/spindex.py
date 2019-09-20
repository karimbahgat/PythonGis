
# various spatial index classes

class Rtree(object):

    def __init__(self, **kwargs):
        backend = kwargs.pop('backend', None)
        if backend is None:
            try:
                self._backend = _RtreeBackend(**kwargs)
            except ImportError:
                self._backend = _PyrTreeBackend(**kwargs)
        elif backend == 'rtree':
            self._backend = _RtreeBackend(**kwargs)
        elif backend == 'pyrtree':
            self._backend = _PyrTreeBackend(**kwargs)
        else:
            raise Exception('No such Rtree backend: {}'.format(backend))

    def insert(self, id, bbox):
        self._backend.insert(id, bbox)

    def intersects(self, bbox):
        return self._backend.intersects(bbox)

    def nearest(self, bbox, **kwargs):
        return self._backend.nearest(bbox, **kwargs)

class QuadTree(object):

    def __init__(self, **kwargs):
        backend = kwargs.pop('backend', None)
        if backend is None or backend == 'pyqtree':
            self._backend = _PyqTreeBackend(**kwargs)
        else:
            raise Exception('No such QuadTree backend: {}'.format(backend))

    def insert(self, id, bbox):
        self._backend.insert(id, bbox)

    def intersects(self, bbox):
        return self._backend.intersects(bbox)

    def nearest(self, bbox, **kwargs):
        return self._backend.nearest(bbox, **kwargs)

# backends

class _RtreeBackend(object):

    def __init__(self, **kwargs):
        import rtree
        self._backend = rtree.index.Index(**kwargs)

    def insert(self, id, bbox):
        self._backend.insert(id, bbox)

    def intersects(self, bbox):
        return self._backend.intersection(bbox)

    def nearest(self, bbox, **kwargs):
        return self._backend.nearest(bbox, **kwargs)

class _PyrTreeBackend(object):

    def __init__(self, **kwargs):
        import pyrtree
        self._backend = pyrtree.RTree(**kwargs)
        self._new_rect = pyrtree.Rect

    def insert(self, id, bbox):
        rect = self._new_rect(*bbox)
        self._backend.insert(id, rect)

    def intersects(self, bbox):
        rect = self._new_rect(*bbox)
        
        res = (node.leaf_obj() for node in self._backend.query_rect(rect)
               if node.is_leaf())
        return res

    def nearest(self, bbox, **kwargs):
        raise NotImplemented

class _PyqTreeBackend(object):

    def __init__(self, **kwargs):
        import pyqtree
        self._backend = pyqtree.Index(**kwargs)

    def insert(self, id, bbox):
        self._backend.insert(id, bbox)

    def intersects(self, bbox):
        return self._backend.intersect(bbox)

    def nearest(self, bbox, **kwargs):
        raise NotImplemented



