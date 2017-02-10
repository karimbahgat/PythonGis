
import pythongis as pg

pg.renderer.DEFAULTSTYLE = "dark"

data = pg.VectorData(r"C:\Users\kimo\Downloads\cshapes_0.6\cshapes.shp",
                     ) #select=lambda f: f["GWSYEAR"]==1946)#.manage.clean(0.1)

def getshps(fs):
    print len(fs)
    return [f.get_shapely() for f in fs]

import shapely, shapely.ops, shapely.speedups
shapely.speedups.enable()
from time import time


# test full
##data.view()
##t = time()
##union = data.aggregate(key=lambda x: True,
##                       geomfunc=lambda fs: shapely.ops.cascaded_union(getshps(fs)).__geo_interface__,
##                       )
##print time() - t
##union.view()


# test tiled
def tiled_union(data):
    for tile in data.manage.tiled(tiles=(5,5)):
        union = tile.aggregate(key=lambda x: True,
                               geomfunc=lambda fs: shapely.ops.cascaded_union(getshps(fs)).__geo_interface__,
                               )
        yield union

t = time()
merged = pg.vector.manager.merge(*list(tiled_union(data)))
final = merged.aggregate(key=lambda x: True,
                           geomfunc=lambda fs: shapely.ops.cascaded_union(getshps(fs)).__geo_interface__,
                           )
print "final time", time() - t
final.view()


