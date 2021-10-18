
import unittest

import pythongis as pg
pg.vector.data.DEFAULT_SPATIAL_INDEX = 'quadtree'

# data

pointdata = pg.VectorData('data/ne_10m_populated_places_simple.shp',
                            encoding='latin')
linedata = pg.VectorData('data/ne_10m_railroads.shp',
                            encoding='latin')
polygondata = pg.VectorData('data/ne_10m_admin_0_countries.shp',
                            encoding='latin')

# base class

class BaseTestCases:

    class DrawShapes(unittest.TestCase):
        width = 600
        height = 300
        kwargs = {'fillcolor':'yellow', 'outlinecolor':'black'}
        output_prefix = 'render_size_units'

        def create_map(self):
            self.map = pg.renderer.Map(self.width, self.height, background='gray')
            #self.map.zoom_in(3)

        def save_map(self, name):
            print('save',self.output_prefix,name)
            self.map.add_legend()
            self.map.save('outputs/{}_{}.png'.format(self.output_prefix, name))

        def test_circle(self):
            self.create_map()
            print(self.kwargs)
            self.map.add_layer(pointdata, **self.kwargs)
            self.save_map('circle')

        def test_pie(self):
            self.create_map()
            print(self.kwargs)
            self.map.add_layer(pointdata, shape='pie', 
                            startangle=0, endangle=110,
                            **self.kwargs)
            self.save_map('pie')

        def test_box(self):
            self.create_map()
            print(self.kwargs)
            self.map.add_layer(pointdata, shape='box', **self.kwargs)
            self.save_map('box')

        def test_triangle(self):
            self.create_map()
            print(self.kwargs)
            self.map.add_layer(pointdata, shape='triangle', **self.kwargs)
            self.save_map('triangle')

        def test_polygon(self):
            self.create_map()
            print(self.kwargs)
            self.map.add_layer(polygondata, **self.kwargs)
            self.save_map('polygon')

        def test_line(self):
            self.create_map()
            print(self.kwargs)
            self.map.add_layer(linedata, **self.kwargs)
            self.save_map('line')

# px

class TestFillPixelUnits(BaseTestCases.DrawShapes):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawShapes, self).__init__(*args, **kwargs)
        self.output_prefix += '_fill_pixel'
        self.kwargs = self.kwargs.copy()
        extra = {'fillsize': '{}px'.format(10)}
        self.kwargs.update(extra)

class TestFillPixelUnitsDynamic(BaseTestCases.DrawShapes):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawShapes, self).__init__(*args, **kwargs)
        self.output_prefix += '_fill_pixel_dynamic'
        self.kwargs = self.kwargs.copy()
        from random import uniform
        dynamic = {'breaks': 'equal', 
                    'key': lambda f: f.bbox[1], #uniform(0,1),
                    'sizes': ['4px', '10px']}
        extra = {'fillsize': dynamic}
        self.kwargs.update(extra)

class TestOutlinePixelUnits(BaseTestCases.DrawShapes):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawShapes, self).__init__(*args, **kwargs)
        self.output_prefix += '_outline_pixel'
        self.kwargs = self.kwargs.copy()
        extra = {'fillsize': '{}px'.format(10),
                'outlinewidth': '{}px'.format(2)}
        self.kwargs.update(extra)

class TestOutlinePixelUnitsDynamic(BaseTestCases.DrawShapes):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawShapes, self).__init__(*args, **kwargs)
        self.output_prefix += '_outline_pixel_dynamic'
        self.kwargs = self.kwargs.copy()
        from random import uniform
        dynamic = {'breaks': 'equal', 
                    'key': lambda f: f.bbox[1], #uniform(0,1),
                    'sizes': ['0.5px', '3px']}
        extra = {'fillsize': '{}px'.format(10),
                'outlinewidth': dynamic}
        self.kwargs.update(extra)

# x/y

class TestFillXUnits(BaseTestCases.DrawShapes):
    
    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawShapes, self).__init__(*args, **kwargs)
        self.output_prefix += '_fill_x'
        self.kwargs = self.kwargs.copy()
        extra = {'fillsize': '{}x'.format(0.5)}
        self.kwargs.update(extra)

class TestOutlineXUnits(BaseTestCases.DrawShapes):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawShapes, self).__init__(*args, **kwargs)
        self.output_prefix += '_outline_x'
        self.kwargs = self.kwargs.copy()
        extra = {'fillsize': '{}x'.format(0.5),
                'outlinewidth': '{}x'.format(0.1)}
        self.kwargs.update(extra)

# pt

class TestFillPointUnits(BaseTestCases.DrawShapes):
    
    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawShapes, self).__init__(*args, **kwargs)
        self.output_prefix += '_fill_point'
        self.kwargs = self.kwargs.copy()
        extra = {'fillsize': '{}pt'.format(1)}
        self.kwargs.update(extra)

class TestOutlinePointUnits(BaseTestCases.DrawShapes):
    
    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawShapes, self).__init__(*args, **kwargs)
        self.output_prefix += '_outline_point'
        self.kwargs = self.kwargs.copy()
        extra = {'fillsize': '{}pt'.format(1),
                'outlinewidth': '{}pt'.format(0.2)}
        self.kwargs.update(extra)

# cm

# mm

# in

# percwidth

# percheight

# percmin

# percmax


if __name__ == '__main__':
    unittest.main()
