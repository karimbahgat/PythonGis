
import pythongis as pg
import gc

countries = pg.VectorData("data/ne_10m_admin_0_countries.shp")
print countries

# mapit
rast = pg.RasterData(r'C:\Users\kimok\Downloads\F182013.v4c_web.stable_lights.avg_vis.tif')

for iso in ['TUR']:
    print iso
    c = countries.select(lambda f: f["ISO_A3"]==iso)
    clip = rast.manage.clip(c, bbox=c.bbox)
    print clip

    mapp = pg.renderer.Map()
    mapp.add_layer(clip)
    mapp.add_layer(c, fillcolor=None)
    mapp.add_legend()
    mapp.view()

    c = c.manage.reproject('+proj=robin')
    clip = clip.manage.reproject('+proj=robin')

    mapp = pg.renderer.Map()
    mapp.add_layer(clip)
    mapp.add_layer(c, fillcolor=None)
    mapp.add_legend()
    mapp.view()






