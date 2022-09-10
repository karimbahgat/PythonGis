
import unittest

import pythongis as pg
pg.vector.data.DEFAULT_SPATIAL_INDEX = 'quadtree'

# data

countrydata = pg.VectorData('data/ne_10m_admin_0_countries.shp',
                            encoding='latin')

# base class

class BaseTestCases:

    class ScalebarMixin(unittest.TestCase):
        width = 600
        height = 300
        kwargs = {'fillcolor':'purple', 'outlinecolor':'black'}
        output_prefix = 'render_scalebar'

        def create_map(self):
            self.map = pg.renderer.Map(self.width, self.height, background='gray')
            self.map.add_layer(countrydata, **self.kwargs)

        def save_map(self, name):
            print('save',self.output_prefix,name)
            self.map.save('outputs/{}_{}.png'.format(self.output_prefix, name))


# tests

class TestScalebarZoom(BaseTestCases.ScalebarMixin):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.ScalebarMixin, self).__init__(*args, **kwargs)
        self.output_prefix += '_zoom'
    
    def test_world(self):
        self.create_map()
        self.map.add_scalebar()
        self.save_map('world')

    def test_france(self):
        self.create_map()
        bbox = countrydata.select(lambda f: f['GEOUNIT']=='France').bbox
        self.map.zoom_bbox(*bbox)
        self.map.add_scalebar()
        self.save_map('france')
    
    def test_gambia(self):
        self.create_map()
        bbox = countrydata.select(lambda f: f['GEOUNIT']=='Gambia').bbox
        self.map.zoom_bbox(*bbox)
        self.map.add_scalebar()
        self.save_map('gambia')





if __name__ == '__main__':
    unittest.main()




