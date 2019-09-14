
# various spatial indexes


# main interface

class Spindex(object):
    
    def __init__(self, type=None):
        if type.lower() == 'rtree':
            try:
                fdsfsd
                self.index = Rtree()
            except:
                self.index = PyrTree()

        elif type.lower() == 'quadtree':
            self.index = PyqTree()

    def insert(self, id, bbox):
        self.index.insert(id, bbox)

    def intersection(self, bbox):
        return self.index.intersection(bbox)

    def nearest(self, bbox, **kwargs):
        return self.index.nearest(bbox, **kwargs)


# backends

class Rtree(object):

    def __init__(self):
        import rtree
        self.backend = rtree.index.Index()

    def insert(self, id, bbox):
        self.backend.insert(id, bbox)

    def intersection(self, bbox):
        return self.backend.intersection(bbox)

    def nearest(self, bbox, **kwargs):
        return self.backend.nearest(bbox, **kwargs)

class PyrTree(object):

    def __init__(self):
        import pyrtree
        self.backend = pyrtree.RTree()
        self.new_rect = pyrtree.Rect

    def insert(self, id, bbox):
        rect = self.new_rect(*bbox)
        self.backend.insert(id, rect)

    def intersection(self, bbox):
        rect = self.new_rect(*bbox)
        
        res = (node.leaf_obj() for node in self.backend.query_rect(rect)
               if node.is_leaf())
        return res

    def nearest(self, bbox, **kwargs):
        raise NotImplemented()

class PyqTree(object):

    def __init__(self):
        raise NotImplemented()




