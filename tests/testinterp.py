
import pythongis as pg
from random import randrange



# GRADIENT TEST
##import pyagg
##c = pyagg.Canvas(500,500)
##c.draw_gradient([(100,400),(290,100)], [(222,0,0),(0,222,0)], 10)
##c.view()




# interp test

def randpoint():
    return (randrange(0,80),randrange(-60,20))

points = pg.vector.data.VectorData()
points.fields = ["val"]
for _ in range(1000):
    points.add_feature(row=[randrange(255)],geometry={"type":"Point","coordinates":randpoint()})

##import pycountries as pc
##clip = pg.vector.data.VectorData()
##for c in pc.Continent("Africa"):
##    clip.add_feature(row=[],
##                     geometry=c.__geo_interface__)
    
clip = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\country_convexes.shp")
clip = pg.vector.manager.crop(clip, [-40,30,80,-80])

rast = pg.raster.analyzer.interpolate(points,
                                      rasterdef={"mode":"int32",
                                                 "width":720,
                                                 "height":360,
                                                 "xy_geo":(-180,90),
                                                 "xy_cell":(0,0),
                                                 "cellwidth":0.5,
                                                 "cellheight":-0.5,
                                                 "nodataval":-99},
                                      valuefield="val",
                                      algorithm="radial",
                                      radius=2)
print rast.bands[0].nodataval
print rast.bands[0].summarystats()
rast = pg.raster.manager.clip(rast, clip, bbox=clip.bbox)
rast.view(1000,500)


