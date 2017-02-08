
import pythongis as pg

data = pg.VectorData(r"C:\Users\kimo\Downloads\cshapes_0.6\cshapes.shp")

pt = pg.VectorData()
pt.add_feature([], dict(type="Point",coordinates=(10,30)))
pt.add_feature([], dict(type="Point",coordinates=(11,31)))

snap = pt.manage.snap(data, 0.5)
for f in snap:
    print f.__geo_interface__
#snap.view()

mapp = pg.renderer.Map()
mapp.add_layer(data)
mapp.add_layer(pt.manage.buffer(lambda f: 0.5))
mapp.add_layer(pt)
mapp.add_layer(snap)
mapp.view()


# test speed (very slow...???)
from random import randrange
pt = pg.VectorData()
for _ in range(4):
    print _
    pt.add_feature([], dict(type="Point",coordinates=(randrange(180),randrange(90))))

snap = pt.manage.snap(data, 1)

mapp = pg.renderer.Map()
mapp.add_layer(data)
mapp.add_layer(pt)
mapp.add_layer(snap)
mapp.view()
