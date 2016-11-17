
# TODO: Add this as a styleoptions option, which auto-generates and pastes this shadow before the rendered image itself

import pythongis as pg

cshapes = pg.VectorData(r"C:\Users\karbah\Downloads\cshapes_0.5-1\cshapes.shp", select=lambda f:f["GWCODE"] != -1)
print cshapes

mapp = pg.renderer.Map(width=1000)
countries = mapp.add_layer(cshapes, fillcolor=dict(breaks="unique"), outlinecolor="white", outlinewidth=0.1)
shadow = mapp.add_layer(cshapes, fillcolor=dict(breaks="unique"), outlinecolor="white", outlinewidth=0.1)
mapp.render_all()
shadow.img = countries.img.offset(5, 10)
shadow.img = shadow.img.point(lambda v: 200 if v > 0 else 0)
mapp.layers.move_layer(1, 0)
mapp.update_draworder()
mapp.view()
