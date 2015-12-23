import pythongis as pg


# load large raster

d = pg.raster.data.RasterData(r"C:\Users\kimo\Downloads\F101992.v4b_web.stable_lights.avg_vis.tif")
    #r"C:\Syria Nightlights\data\nightlights\priogridones\F101993.v4b_web.stable_lights.avg_vis.tif")
#d.view(1000,500)
print d


# crop test

c = pg.raster.manager.crop(d, [-80,35,0,0])
print c
c.view(1000,500)



# resample test

r = pg.raster.manager.resample(c, bbox=c.bbox, #[-150,60,-60,10],
                               xscale=0.5, yscale=-0.5,
                               algorithm="nearest")
#r.bands[0].nodataval = 0
#r.bands[0].mask
print r

r.view(1000,500)

