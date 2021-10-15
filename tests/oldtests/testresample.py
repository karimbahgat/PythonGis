import pythongis as pg



# load large raster

d = pg.raster.data.RasterData(#r"C:\Users\kimo\Downloads\F101992.v4b_web.stable_lights.avg_vis.tif")
    r"C:\Syria Nightlights\data\nightlights\priogridones\F101993.v4b_web.stable_lights.avg_vis.tif")
#d.view(1000,500)
print d


# crop test

c = pg.raster.manager.crop(d, [35.700798, 32.312938, 42.349591, 37.229873]) #[-150,55,0,0])
print c
c.view(1000,500)




# tiled test
##for t in pg.raster.manager.tiled(c, tiles=(2,2)):
##    print t
##    t.view(500,500)




# aggregate stats resampling (better for aggregate types of data)
agg = pg.raster.manager.upscale(c, 
                                bbox=c.bbox, xscale=0.1, yscale=0.1,
                                stat="sum")
print agg
print agg.bands[0].summarystats()
agg.view(1000,500)


# resample test (better for sampled continuous interpolation type data)

r = pg.raster.manager.resample(c, bbox=c.bbox, #[-150,60,-60,10],
                               xscale=0.1, yscale=0.1,
                               algorithm="bilinear")
#r.bands[0].nodataval = 0
#r.bands[0].mask
print r

r.view(1000,500)

