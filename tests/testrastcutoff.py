
import pythongis as pg
import gc

countries = pg.VectorData(r"C:\Users\kimok\Desktop\ch est\data\cshapes.shp")
countries = countries.select(lambda f: f["GWCODE"] != -1 and f["GWEYEAR"] == 2016)
print countries

# mapit
#rast = pg.RasterData(r'C:\Users\kimok\Downloads\F182013.v4c_web.stable_lights.avg_vis.tif')
rast = pg.RasterData(r'C:\Users\kimok\Downloads\SVDNB_npp_20170701-20170731_75N060W_vcmcfg_v10_c201708061230.avg_rade9.tif')
print rast

for iso in ['NGA','COD','YEM']:
    print iso
    c = countries.select(lambda f: f["ISO1AL3"]==iso)
    clip = rast.manage.clip(c, bbox=c.bbox)
    print clip
    clip.view(cutoff=(0.1,99.9))

print 'finished!'



