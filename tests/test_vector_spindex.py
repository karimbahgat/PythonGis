
import unittest

import pythongis as pg

# data

pointdata = pg.VectorData('data/ne_10m_populated_places_simple.shp',
                            encoding='latin')

# base class

class BaseTestCases:

    class TestInitSpindex(unittest.TestCase):

        def create_spindex(self, **kwargs):
            self.data.create_spatial_index(**kwargs)

        def test_default_rtree(self):
            # on local pc should fail and fallback to quadtree
            pg.vector.data.DEFAULT_SPATIAL_INDEX = 'rtree'
            self.create_spindex()
            self.assertTrue(hasattr(self.data, 'spindex'))
            self.assertTrue(not isinstance(self.data.spindex, pg.vector.spindex.Rtree))

        def test_default_quadtree(self):
            pg.vector.data.DEFAULT_SPATIAL_INDEX = 'quadtree'
            self.create_spindex()
            self.assertTrue(hasattr(self.data, 'spindex'))
            self.assertTrue(isinstance(self.data.spindex, pg.vector.spindex.QuadTree))

        def test_rtree(self):
            # on local pc should fail and fallback to quadtree
            self.create_spindex(type='rtree')
            self.assertTrue(hasattr(self.data, 'spindex'))
            self.assertTrue(not isinstance(self.data.spindex, pg.vector.spindex.Rtree))

        def test_quadtree(self):
            self.create_spindex(type='quadtree')
            self.assertTrue(hasattr(self.data, 'spindex'))
            self.assertTrue(isinstance(self.data.spindex, pg.vector.spindex.QuadTree))



# tests

class TestInitPointData(BaseTestCases.TestInitSpindex):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.TestInitSpindex, self).__init__(*args, **kwargs)
        self.data = pointdata.copy()
    
    





if __name__ == '__main__':
    unittest.main()




