
import unittest

import pythongis as pg
pg.vector.data.DEFAULT_SPATIAL_INDEX = 'quadtree'

# data

countrydata = pg.VectorData('data/ne_10m_admin_0_countries.shp',
                            encoding='latin')

# base class

class BaseTestCases:

    class NavigateMixin(unittest.TestCase):
        width = 600
        height = 300
        kwargs = {'fillcolor':'purple', 'outlinecolor':'black'}
        output_prefix = 'render_navigate'

        def create_map(self):
            self.map = pg.renderer.Map(self.width, self.height, background='gray')
            self.map.add_layer(countrydata, **self.kwargs)

        def save_map(self, name):
            print('save',self.output_prefix,name)
            self.map.save('outputs/{}_{}.png'.format(self.output_prefix, name))


# tests

class TestZoomIn(BaseTestCases.NavigateMixin):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.NavigateMixin, self).__init__(*args, **kwargs)
        self.output_prefix += '_zoom_in'
    
    def test_2x(self):
        self.create_map()
        self.map.zoom_in(2)
        self.save_map('2x')

    def test_5x_center(self):
        self.create_map()
        self.map.zoom_in(5, center=(2,49)) # paris
        self.save_map('5x_paris')

class TestZoomOut(BaseTestCases.NavigateMixin):
    
    def __init__(self, *args, **kwargs):
        super(BaseTestCases.NavigateMixin, self).__init__(*args, **kwargs)
        self.output_prefix += '_zoom_out'
    
    def test_2x(self):
        self.create_map()
        self.map.zoom_out(2)
        self.save_map('2x')

    def test_5x_center(self):
        self.create_map()
        self.map.zoom_out(5, center=(2,49)) # paris
        self.save_map('5x_paris')

class TestMulti(BaseTestCases.NavigateMixin):
    
    def __init__(self, *args, **kwargs):
        super(BaseTestCases.NavigateMixin, self).__init__(*args, **kwargs)
        self.output_prefix += '_multi'
    
    def test_zoom_offset(self):
        self.create_map()
        self.map.zoom_in(2)
        self.map.offset(180, 90) # topright
        self.save_map('zoom_offset')

    def test_offset_offset(self):
        self.create_map()
        self.map.offset(180, 90) # topright
        self.map.offset(-360, -180) # reverse to bottomleft
        self.save_map('offset_offset')



if __name__ == '__main__':
    unittest.main()




