
import unittest

import pythongis as pg
pg.vector.data.DEFAULT_SPATIAL_INDEX = 'quadtree'

# data

pointdata = pg.VectorData('data/ne_10m_populated_places_simple.shp',
                            encoding='latin')
worldcities = pointdata.select(lambda f: f['worldcity']==1)
polygondata = pg.VectorData('data/ne_10m_admin_0_countries.shp',
                            encoding='latin')

# base class

class BaseTestCases:

    class DrawDatasets(unittest.TestCase):
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

    class DrawInspect(unittest.TestCase):
        width = 1000
        height = 500
        multiline = False
        kwargs = {'fillcolor':'yellow', 'outlinecolor':'black',
                'textoptions':{}}
        output_prefix = 'render_text'

        def create_map(self):
            self.map = pg.renderer.Map(self.width, self.height, background='gray')
            #self.map.zoom_in(3)

        def save_map(self, name):
            print('save',self.output_prefix,name)
            self.map.save('outputs/{}_{}.png'.format(self.output_prefix, name))

        def test_worldcities(self):
            self.create_map()
            kwargs = self.kwargs.copy()
            if self.multiline:
                extra = {'text': lambda f: '\n'.join(f['name'].split())}
            else:
                extra = {'text': lambda f: f['name']}
            kwargs.update(extra)
            self.map.add_layer(worldcities, **kwargs)
            self.save_map('worldcities')

### 

class TestDefaultTextOptions(BaseTestCases.DrawDatasets):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawDatasets, self).__init__(*args, **kwargs)
        self.output_prefix += '_default_opts'
        self.kwargs = self.kwargs.copy()
        textopts = {'xy':'midpoint'}
        self.kwargs['textoptions'] = textopts

class TestSmallFont(BaseTestCases.DrawDatasets):
    
    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawDatasets, self).__init__(*args, **kwargs)
        self.output_prefix += '_small_font'
        self.kwargs = self.kwargs.copy()
        textopts = {'xy':'midpoint', 
                    'textsize':6}
        self.kwargs['textoptions'] = textopts

class TestDefaultAnchor(BaseTestCases.DrawInspect):
    
    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawInspect, self).__init__(*args, **kwargs)
        self.output_prefix += '_anchor_default'
        self.kwargs = self.kwargs.copy()
        textopts = {'xy':'midpoint'}
        self.kwargs['textoptions'] = textopts

class TestSWAnchor(BaseTestCases.DrawInspect):
    
    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawInspect, self).__init__(*args, **kwargs)
        self.output_prefix += '_anchor_sw'
        self.kwargs = self.kwargs.copy()
        textopts = {'xy':'midpoint', 'anchor':'sw'}
        self.kwargs['textoptions'] = textopts

class TestJustifyDefault(BaseTestCases.DrawInspect):
    
    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawInspect, self).__init__(*args, **kwargs)
        self.multiline = True
        self.output_prefix += '_justify_default'
        self.kwargs = self.kwargs.copy()
        textopts = {'xy':'midpoint'}
        self.kwargs['textoptions'] = textopts

class TestJustifyRight(BaseTestCases.DrawInspect):
    
    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawInspect, self).__init__(*args, **kwargs)
        self.multiline = True
        self.output_prefix += '_justify_right'
        self.kwargs = self.kwargs.copy()
        textopts = {'xy':'midpoint', 'justify':'right'}
        self.kwargs['textoptions'] = textopts

class TestJustifyCenter(BaseTestCases.DrawInspect):
    
    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawInspect, self).__init__(*args, **kwargs)
        self.multiline = True
        self.output_prefix += '_justify_center'
        self.kwargs = self.kwargs.copy()
        textopts = {'xy':'midpoint', 'justify':'center'}
        self.kwargs['textoptions'] = textopts



if __name__ == '__main__':
    unittest.main()
