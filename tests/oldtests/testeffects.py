
import pythongis as pg

poly = pg.VectorData("data/ne_10m_admin_0_countries.shp")

mapp = pg.renderer.Map(1000,500,background=None) #,background=(255,0,0))
lyr = mapp.add_layer(poly)


lyr.add_effect("inner", color=[(255,111,111,255),(255,111,111,0)], size=10)
#lyr.add_effect("glow", color=[(111,111,255,255),(211,211,255,0)], size=10)
lyr.add_effect("shadow", xdist=10, ydist=10)

mapp.view()












# OLD

# TODO: Add this as a styleoptions option, which auto-generates and pastes this shadow before the rendered image itself
##cshapes = pg.VectorData(r"C:\Users\kimo\Downloads\cshapes_0.6\cshapes.shp", select=lambda f:f["GWCODE"] != -1)
##print cshapes
##
##mapp = pg.renderer.Map(width=1000)
##countries = mapp.add_layer(cshapes, fillcolor=dict(breaks="unique"), outlinecolor="white", outlinewidth=0.1)
##shadow = mapp.add_layer(cshapes, fillcolor=dict(breaks="unique"), outlinecolor="white", outlinewidth=0.1)
##mapp.render_all()
##shadow.img = countries.img.offset(5, 10)
##shadow.img = shadow.img.point(lambda v: 200 if v > 0 else 0)
##mapp.layers.move_layer(1, 0)
##mapp.update_draworder()
##mapp.view()
