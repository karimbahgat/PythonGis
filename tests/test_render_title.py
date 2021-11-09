
import unittest

import pythongis as pg

# data
pointdata = pg.VectorData('data/ne_10m_populated_places_simple.shp',
                            encoding='latin')

# base class

class BaseTestCases:

    class TitleMixin(unittest.TestCase):
        width = 600
        height = 300
        kwargs = {'fillcolor':'yellow', 'outlinecolor':'black'}
        output_prefix = 'render_title'

        def create_map(self):
            self.map = pg.renderer.Map(self.width, self.height, background='gray')
            #self.map.zoom_in(3)

        def save_map(self, name):
            print('save',self.output_prefix,name)
            self.map.title = 'Map Title'
            self.map.save('outputs/{}_{}.png'.format(self.output_prefix, name))


# tests

class TestTitleBox(BaseTestCases.TitleMixin):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.TitleMixin, self).__init__(*args, **kwargs)
        self.output_prefix += '_box'
    
    def test_default(self):
        self.create_map()
        kwargs = self.kwargs.copy()
        self.map.add_layer(pointdata, **kwargs)
        self.map.titleoptions = {}
        self.save_map('default')

    def test_nobox(self):
        self.create_map()
        kwargs = self.kwargs.copy()
        self.map.add_layer(pointdata, **kwargs)
        self.map.titleoptions = {'fillcolor':None, 'outlinecolor':None}
        self.save_map('nobox')


class TestTitlePlacement(BaseTestCases.TitleMixin):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.TitleMixin, self).__init__(*args, **kwargs)
        self.output_prefix += '_placement'
    
    def test_topcenter(self):
        self.create_map()
        kwargs = self.kwargs.copy()
        self.map.add_layer(pointdata, **kwargs)
        self.map.titleoptions = {'xy':('50%w','1%h'), 'anchor':'n'}
        self.save_map('topcenter')

    def test_nw(self):
        self.create_map()
        kwargs = self.kwargs.copy()
        self.map.add_layer(pointdata, **kwargs)
        self.map.titleoptions = {'xy':('1%w','1%h'), 'anchor':'nw'}
        self.save_map('nw')

    def test_ne(self):
        self.create_map()
        kwargs = self.kwargs.copy()
        self.map.add_layer(pointdata, **kwargs)
        self.map.titleoptions = {'xy':('99%w','1%h'), 'anchor':'ne'}
        self.save_map('ne')

    def test_se(self):
        self.create_map()
        kwargs = self.kwargs.copy()
        self.map.add_layer(pointdata, **kwargs)
        self.map.titleoptions = {'xy':('99%w','99%h'), 'anchor':'se'}
        self.save_map('se')

    def test_sw(self):
        self.create_map()
        kwargs = self.kwargs.copy()
        self.map.add_layer(pointdata, **kwargs)
        self.map.titleoptions = {'xy':('1%w','99%h'), 'anchor':'sw'}
        self.save_map('sw')



        




if __name__ == '__main__':
    unittest.main()




