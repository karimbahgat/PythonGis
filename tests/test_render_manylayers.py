
import unittest

import pythongis as pg
pg.vector.data.DEFAULT_SPATIAL_INDEX = 'quadtree'

# data

rasterdata = pg.RasterData('data/land_shallow_topo_2048.png')
rasterdata.set_geotransform(width=2048, height=1024,
                           affine=[0.175781250,0,-180,0,-0.175781250,90])
countrydata = pg.VectorData('data/ne_10m_admin_0_countries.shp',
                            encoding='latin')
admindata = pg.VectorData('data/ne_10m_admin_1_states_provinces.shp',
                            encoding='latin')
pointdata = pg.VectorData('data/ne_10m_populated_places_simple.shp',
                            encoding='latin')

# base class

class BaseTestCases:

    class BaseMixin(unittest.TestCase):
        width = 1200
        height = 600
        output_prefix = 'render'

        def create_map(self):
            self.map = pg.renderer.Map(self.width, self.height, background='gray')

        def save_map(self, name):
            print('save',self.output_prefix,name)
            self.map.save('outputs/{}_{}.png'.format(self.output_prefix, name))


# tests

class TestManyLayers(BaseTestCases.BaseMixin):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.BaseMixin, self).__init__(*args, **kwargs)
        self.output_prefix += '_manylayers'
    
    def test_1(self):
        self.create_map()
        self.map.add_layer(rasterdata)
        self.map.add_layer(pointdata, fillcolor='red', fillsize='1px', outlinecolor=None)
        self.map.add_layer(admindata, fillcolor=None, outlinecolor='orange', outlinewidth='0.3px')
        self.map.add_layer(countrydata, fillcolor=None)
        self.save_map('1')





if __name__ == '__main__':
    unittest.main()




