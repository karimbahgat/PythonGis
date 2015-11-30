
import pythongis as pg

### RASTER
##print ""
##print "RASTER"
##
### ...
##print ""
##print "local math"
###raster1 = pg.Raster("test_files/geotiff/gl_anthrome.tif")
##raster2 = pg.Raster("test_files/geotiff/TrueMarble.16km.2700x1350.tif")
##raster1 = pg.Raster("test_files/geotiff/eu_anthrome.tif")
###raster2 = pg.Raster("test_files/geotiff/as_anthrome.tif")
##rastermath = pg.raster.analyzer.math("raster2 ^ raster1", raster1, raster2)
##print rastermath.getcolors()
##import PIL.ImageOps
##img = PIL.ImageOps.equalize(rastermath.convert("L"))
##img.save(r"C:\Users\kimo\Desktop\math211.png")
##
##
print ""
print "zonal stats"
zonaldata = pg.Raster("test_files/geotiff/gl_anthrome.tif")
valuedata = pg.Raster("test_files/geotiff/TrueMarble.16km.2700x1350.tif")
#zonaldata = pg.Raster("test_files/geotiff/eu_anthrome.tif")
#valuedata = pg.Raster("test_files/geotiff/as_anthrome.tif")
stats,resultraster = pg.raster.analyzer.zonal_statistics(zonaldata, valuedata)
for zone,stats in stats.items():
    print zone
    for type,val in stats.items():
        print "  ", type, val
resultraster.grids[0].img.convert("RGBA").save(r"C:\Users\kimo\Desktop\zonalstat.png")




### VECTOR
print ""
print "VECTOR"

# Overlay analysis

print ""
print "overlap summary"
print "polygons"
groupbydata = pg.GeoTable("test_files/shp/cshapes.shp")
valuedata = pg.GeoTable("test_files/shp/domestic.shp")
#groupbydata = pg.vector.manager.vector_clean(groupbydata)
##for feat in reversed(groupbydata):
##    if feat["CNTRY_NAME"] not in ("Saudi Arabia","Norway","Egypt","Denmark","Turkey"):
##        del groupbydata.features[feat.id]
summarized = pg.vector.analyzer.overlap_summary(groupbydata, valuedata,
                                                fieldmapping=[("inc_count","sum"),
                                                              ("Average_nk","average"),
                                                              ("Average_nw","average")] )
summarized.save("test_files/summary.shp")

##print ""
##print "intersect"
##print "polygons"
##data1 = pg.GeoTable("test_files/shp/domestic.shp")
##data2 = pg.GeoTable("test_files/shp/cshapes.shp")
##for feat in reversed(data2):
##    if feat["CNTRY_NAME"] != "Saudi Arabia":
##        del data2.features[feat.id]
###print len(data2), data2.features
##joined = pg.vector.analyzer.vector_spatialjoin(data1, data2, "intersects")#"distance", radius=10)
##joined.save("test_files/spajoin.shp")

print ""
print "viewing results"
layergroup = pg.renderer.LayerGroup()
#layer = pg.renderer.VectorLayer(data1)
#layergroup.add_layer(layer)
layer = pg.renderer.VectorLayer(summarized)
layergroup.add_layer(layer)
#layer = pg.renderer.VectorLayer(data2)
#layergroup.add_layer(layer)
mapp = pg.renderer.MapCanvas(layergroup,1000,500)
mapp.render_all()
mapp.view()

# ...

# Distance analysis

print ""
print "buffering"
#print "points"
#data = pg.GeoTable("test_files/shp/domestic.shp")
#buffered = pg.vector.analyzer.vector_buffer(data, """float(feat["Average_nk"])/30.0""")
##print "lines"
##data = pg.GeoTable("test_files/shp/international.shp")
##buffered = pg.vector.analyzer.vector_buffer(data, "1") #"""float(feat["gnat_x"])/1000.0""")
print "polygons"
data = pg.GeoTable("test_files/shp/cshapes.shp")
buffered = pg.vector.analyzer.vector_buffer(data, "0.7")

print ""
print "viewing results"
layergroup = pg.renderer.LayerGroup()
layer = pg.renderer.VectorLayer(buffered)
layergroup.add_layer(layer)
mapp = pg.renderer.MapCanvas(layergroup,1000,500)
mapp.render_all()
mapp.view()

