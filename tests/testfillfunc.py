
import pythongis as pg

poly = pg.VectorData("data/ne_10m_admin_0_countries.shp")

def filleffect(feat):
    sdfdsf

mapp = pg.renderer.Map(1000,500,background=None) #,background=(255,0,0))
lyr = mapp.add_layer(poly, fillcolor=filleffect)
mapp.view()



