
import unittest

import pythongis as pg
pg.vector.data.DEFAULT_SPATIAL_INDEX = 'quadtree'

# data

pointdata = pg.VectorData('data/ne_10m_populated_places_simple.shp',
                            encoding='latin')
polygondata = pg.VectorData('data/ne_10m_admin_0_countries.shp',
                            encoding='latin')

# base class

class BaseTestCases:

    class DrawText(unittest.TestCase):
        width = 600
        height = 300
        kwargs = {'fillcolor':'yellow', 'outlinecolor':'black',
                'textoptions':{}}
        output_prefix = 'render_text'

        def create_map(self):
            self.map = pg.renderer.Map(self.width, self.height, background='gray')
            #self.map.zoom_in(3)

        def save_map(self, name):
            print('save',self.output_prefix,name)
            self.map.save('outputs/{}_{}.png'.format(self.output_prefix, name))

        def test_countrynames(self):
            self.create_map()
            kwargs = self.kwargs.copy()
            extra = {'text': lambda f: f['GEOUNIT']}
            kwargs.update(extra)
            self.map.add_layer(polygondata, **kwargs)
            self.save_map('countrynames')

        def test_placenames(self):
            self.create_map()
            kwargs = self.kwargs.copy()
            extra = {'text': lambda f: f['name']}
            kwargs.update(extra)
            self.map.add_layer(pointdata, **kwargs)
            self.save_map('placenames')

### 

class TestDefaultTextOptions(BaseTestCases.DrawText):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawText, self).__init__(*args, **kwargs)
        self.output_prefix += '_default_opts'
        self.kwargs = self.kwargs.copy()
        textopts = {'xy':'midpoint'}
        self.kwargs['textoptions'] = textopts

class TestSmallFont(BaseTestCases.DrawText):
    
    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawText, self).__init__(*args, **kwargs)
        self.output_prefix += '_small_font'
        self.kwargs = self.kwargs.copy()
        textopts = {'xy':'midpoint', 
                    'textsize':6}
        self.kwargs['textoptions'] = textopts



if __name__ == '__main__':
    unittest.main()
