
import pythongis as pg
from random import randrange

# resample
##import PIL,PIL.Image
##raster = pg.raster.data.RasterData(filepath="world.jpg", **{"xy_cell":(0,0),
##                                                            "xy_geo":(-180,90),
##                                                             "cellwidth":318/360.0,
##                                                             "cellheight":-159/180.0}
##                                   )
##print raster
##PIL.Image.merge("RGB", [b.img.convert("L") for b in raster]).show()
##
##trans = pg.raster.manager.resample(raster, rasterdef={"width":720, #"affine":[0.5,1,-180, 0,-0.5,90]})
##                                                     "height":360,
##                                                     "xy_geo":(0,0),
##                                                     "xy_cell":(0,0),
##                                                     "cellwidth":0.5,
##                                                     "cellheight":-0.5})
##print trans
##PIL.Image.merge("RGB", [b.img.convert("L") for b in trans]).show()
##
##fdasfas


# GRADIENT TEST
import pyagg
c = pyagg.Canvas(500,500)
c.draw_gradient([(100,400),(290,100)], [(222,0,0),(0,222,0)], 10)
c.view()


# interp test

def randpoint():
    return (randrange(0,80),randrange(-60,20))

points = pg.vector.data.VectorData()
points.fields = ["val"]
for _ in range(1000):
    points.add_feature(row=[randrange(255)],geometry={"type":"Point","coordinates":randpoint()})

import pycountries as pc
clip = pg.vector.data.VectorData()
for c in pc.Continent("Africa"):
    clip.add_feature(row=[],
                     geometry=c.__geo_interface__)

rast = pg.raster.analyzer.interpolate(points,
                                      rasterdef={"mode":"I",
                                                 "width":720,
                                                 "height":360,
                                                 "xy_geo":(-180,90),
                                                 "xy_cell":(0,0),
                                                 "cellwidth":0.5,
                                                 "cellheight":-0.5,
                                                 "nodataval":-99},
                                      valuefield="val",
                                      algorithm="circular",
                                      radius=2)
rast = pg.raster.manager.clip(rast, clip)

lyr = pg.renderer.RasterLayer(rast)
lyr.render(500,500)
print lyr.img.getextrema()
lyr.img.show()

#lyr.img.save(r"\\GRID\karbah\PROFILE\Desktop\bleh.png")

#rast.bands[0].img.show()
