import pythongis as pg

d = pg.raster.data.RasterData(r"C:\Syria Nightlights\data\nightlights\priogridones\F101993.v4b_web.stable_lights.avg_vis.tif")

#d.bands[0].nodataval = 0
#d.bands[0].mask

print d
print d.bands[0].summarystats()

r = pg.raster.manager.resample(d, bbox=[-150,60,-60,10],
                               xscale=0.5, yscale=-0.5,
                               algorithm="nearest")
r.bands[0].nodataval = 0
r.bands[0].mask
##r.bands[0].img.save(r"\\GRID\karbah\PROFILE\Desktop\bleh2.png")

print r
print r.bands[0].summarystats()
print r.bands[0].img.getcolors()

lyr = pg.renderer.RasterLayer(r, minval=3, maxval=63, gradcolors=[(255,0,0),(0,255,0)])
lyr.render(width=500,height=250,resampling="nearest")
print lyr.img.size
lyr.img.show()

##prev = 0
##px = d.bands[0].img.load()
##for y in xrange(d.height):
##    if y-prev >=100:
##        prev = y
##        print y
##    for x in xrange(d.width):
##        px[x,y]

# crop test
