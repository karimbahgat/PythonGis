
import pythongis as pg

cshapes = pg.VectorData("cshapes.shp", select=lambda f:f["GWCODE"] != -1)
cshapes = pg.VectorData("selfisec.geojson")
print cshapes

mapp = pg.renderer.Map(width=1000)
mapp.add_layer(cshapes, fillcolor="blue")

selfint = cshapes.intersections()
print selfint
selfint.view(1000,1000,flipy=1,fillcolor=pg.renderer.Color("red",opacity=155))

selfint = selfint.duplicates(fieldmapping=[("count",lambda f:1,"count")])
print selfint

mapp.add_layer(selfint, fillcolor=pg.renderer.Color("red",opacity=155))
mapp.render_all()
mapp.view()
