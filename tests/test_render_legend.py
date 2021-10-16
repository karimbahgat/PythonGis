
import unittest

import pythongis as pg
pg.vector.data.DEFAULT_SPATIAL_INDEX = 'quadtree'

# data

pointdata = pg.VectorData('data/ne_10m_populated_places_simple.shp',
                            encoding='latin')

# base class

class BaseTestCases:

    class LegendMixin(unittest.TestCase):
        width = 600
        height = 300
        kwargs = {'fillcolor':'yellow', 'outlinecolor':'black'}
        output_prefix = 'render_legend'

        def create_map(self):
            self.map = pg.renderer.Map(self.width, self.height, background='gray')
            #self.map.zoom_in(3)

        def save_map(self, name):
            print('save',self.output_prefix,name)
            self.map.add_legend()
            self.map.save('outputs/{}_{}.png'.format(self.output_prefix, name))


# tests

class TestValueFormat(BaseTestCases.LegendMixin):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.LegendMixin, self).__init__(*args, **kwargs)
        self.output_prefix += '_value_format'
    
    def test_default_millions(self):
        self.create_map()
        kwargs = self.kwargs.copy()
        from random import uniform
        kwargs['fillsize'] = {'key':lambda f: uniform(0,2000000),
                                'sizes':['3px','10px']}
        self.map.add_layer(pointdata, **kwargs)
        self.save_map('default_milions')

    def test_default_hundred(self):
        self.create_map()
        kwargs = self.kwargs.copy()
        from random import uniform
        kwargs['fillsize'] = {'key':lambda f: uniform(0,100),
                                'sizes':['3px','10px']}
        self.map.add_layer(pointdata, **kwargs)
        self.save_map('default_hundred')

    def test_default_ten(self):
        self.create_map()
        kwargs = self.kwargs.copy()
        from random import uniform
        kwargs['fillsize'] = {'key':lambda f: uniform(0,10),
                                'sizes':['3px','10px']}
        self.map.add_layer(pointdata, **kwargs)
        self.save_map('default_ten')

    def test_default_one(self):
        self.create_map()
        kwargs = self.kwargs.copy()
        from random import uniform
        kwargs['fillsize'] = {'key':lambda f: uniform(0,1),
                                'sizes':['3px','10px']}
        self.map.add_layer(pointdata, **kwargs)
        self.save_map('default_one')





if __name__ == '__main__':
    unittest.main()




