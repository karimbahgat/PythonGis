
import pythongis as pg
from time import time

# test distance
vect = pg.VectorData(r"C:\Users\kimo\Downloads\cshapes_0.6\cshapes.shp",
                     )#select=lambda f: f["GWCODE"]==666)
hist = vect.histogram("GWCODE")
#hist.view()

t = time()
distrast = pg.raster.analyzer.distance(vect, bbox=[-180,90,180,-90], width=72*5, height=36*5)
#distrast = pg.RasterData("C:/Users/kimo/Desktop/world.jpg", bbox=[-180,90,180,-90], width=512, height=256)
print time()-t

hist = distrast.bands[0].histogram()
print hist
#hist.view()

#mapp = distrast.render()
mapp = pg.renderer.Map()
mapp.add_layer(distrast)
mapp.add_layer(vect, fillcolor=None)
#mapp.add_legend()
mapp.view()

