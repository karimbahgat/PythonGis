
import unittest

import pythongis as pg

# data

pointdata = pg.VectorData('data/ne_10m_populated_places_simple.shp',
                            encoding='latin')
linedata = pg.VectorData('data/ne_10m_railroads.shp',
                            encoding='latin')
polygondata = pg.VectorData('data/ne_10m_admin_0_countries.shp',
                            encoding='latin')
rasterdata = pg.RasterData('data/land_shallow_topo_2048.png')
rasterdata.set_geotransform(width=2048, height=1024,
                           affine=[0.175781250,0,-180,0,-0.175781250,90])

# base class

class BaseTestCases:

    class DrawShapes(unittest.TestCase):
        width = 600
        height = 300
        kwargs = {'fillcolor':'yellow', 'outlinecolor':'black'}
        output_prefix = 'render_projections'
        crs = None

        def create_map(self):
            self.map = pg.renderer.Map(self.width, self.height, background='gray',
                                       crs=self.crs)
            self.map.zoom_in(1.5)

        def save_map(self, name):
            print('save',self.output_prefix,name)
            #self.map.add_legend()
            self.map.save('outputs/{}_{}.png'.format(self.output_prefix, name))

        def test_circle(self):
            self.create_map()
            print(self.kwargs)
            self.map.add_layer(pointdata, **self.kwargs)
            self.save_map('circle')

        def test_polygon(self):
            self.create_map()
            print(self.kwargs)
            self.map.add_layer(polygondata, **self.kwargs)
            self.save_map('polygon')

        # def test_line(self):
        #     self.create_map()
        #     print(self.kwargs)
        #     self.map.add_layer(linedata, **self.kwargs)
        #     self.save_map('line')

        def test_raster(self):
            self.create_map()
            print(self.kwargs)
            self.map.add_layer(rasterdata)
            self.save_map('raster')

# projections

class TestDefault(BaseTestCases.DrawShapes):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawShapes, self).__init__(*args, **kwargs)
        self.output_prefix += '_default'
        self.crs = None

class TestRobinson(BaseTestCases.DrawShapes):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawShapes, self).__init__(*args, **kwargs)
        self.output_prefix += '_robinson'
        self.crs = '+proj=robin +lon_0=0 +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs'

class TestMercator(BaseTestCases.DrawShapes):

    def __init__(self, *args, **kwargs):
        super(BaseTestCases.DrawShapes, self).__init__(*args, **kwargs)
        self.output_prefix += '_mercator'
        self.crs = '+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +wktext  +no_defs'



if __name__ == '__main__':
    unittest.main()
