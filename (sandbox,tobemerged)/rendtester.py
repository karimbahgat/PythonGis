import pythongis as pg
import pyagg
import time



##############
# load layers
layers = pg.LayerGroup()

##data = pg.Raster(r"C:\Users\kimo\Dropbox\pygeo book 2\code\test_files\geotiff\SP27GTIF.TIF")
##data.info["nodata_value"] = 0
##lyr = pg.RasterLayer(data)
##layers.add_layer(lyr)

data = pg.GeoTable(r"C:\Users\kimo\Dropbox\pygeo book 2\code\test_files\shp\necountries.shp", encoding="latin")
#data = pg.GeoTable(r"C:\Users\kimo\Desktop\gadm2.shp", encoding="latin")
lyr = pg.VectorLayer(data, fillcolor=None, outlinecolor="red", outlinewidth=0.2)
layers.add_layer(lyr)

#data = pg.GeoTable(r"C:\Users\kimo\Dropbox\pygeo book 2\code\test_files\gpx\track-with-extremes.gpx")
#lyr = pg.VectorLayer(data, fillcolor="white")
#layers.add_layer(lyr)

##################
# render layers in multiple independent maps
print "layers loaded, now rendering..."
t = time.clock()

# zoom full world
world = pg.MapCanvas(layers,1000,500,(0,222,0))
world.render_all()
world.img.save("test_renders/world.png")
#world.drawer.view()

### zoom 4x
##closeup = pg.MapCanvas(layers,1000,500,(0,222,0))
##closeup.zoom_factor(4)
##closeup.render_all()
##closeup.img.save("test_renders/4x.png")
###closeup.drawer.view()
##
### zoom to last data extent
##tracks = pg.MapCanvas(layers,1000,500,(0,222,0))
##xmin,ymin,xmax,ymax = data.bbox
##tracks.zoom_bbox(xmin,ymax,xmax,ymin) # to center in on
##tracks.zoom_factor(-1.1)
##tracks.render_all()
##tracks.img.save("test_renders/tracks.png")
###tracks.drawer.view()

# slow zoom
##for z in range(1,30):
##    z = 1+z/10.0
##    closeup = pg.MapCanvas(layers,1000,500,(0,222,0))
##    closeup.zoom_factor(z)
##    closeup.render_all()
##    print z
##    #closeup.img.save("test_renders/%ix.png" %z)

print "all map zooms rendered and saved in %s secs" %str(time.clock()-t)




