
import pythongis as pg

data = pg.VectorData(r"C:\Users\kimo\Downloads\cshapes_0.6\cshapes.shp")

cutter = pg.VectorData()
cutter.add_feature([], dict(type="LineString",coordinates=[(-180,60),(180,-60)]))

after = data.manage.cut(cutter)

mapp = pg.renderer.Map()
mapp.add_layer(data)
mapp.add_layer(cutter)
mapp.add_layer(after)
mapp.view()

