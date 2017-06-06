import pythongis as pg
from time import time

#d = pg.VectorData(r"C:\Users\kimo\Downloads\ne_10m_admin_1_states_provinces\ne_10m_admin_1_states_provinces.shp", encoding="latin")
d = pg.VectorData(r"C:\Users\kimo\Downloads\cshapes_0.6\cshapes.shp", encoding="latin")
d = d.select(lambda f: f["GWEYEAR"]==2016)
#d = pg.VectorData(r"C:\Users\kimo\Downloads\qs_adm1\qs_adm1.shp", encoding="latin")
#p = pg.VectorData(r"C:\Users\kimo\Downloads\ne_10m_populated_places\ne_10m_populated_places.shp")

mapp = pg.renderer.Map(1000, 500)
mapp.add_layer(d)
#mapp.add_layer(p, fillsize=0.3)#, text=lambda f: f["NAME"], textoptions=dict(textsize=5))
mapp.view()
