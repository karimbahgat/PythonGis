
import pythongis as pg

###############
# VECTOR DATA
###############

##print "VECTOR TESTS"
##
##data1 = pg.GeoTable("test_files/geoj/cshapes.geo.json")
##data2 = pg.GeoTable("test_files/shp/cshapes.shp")
##
### to points
##print "to points, centroid"
##centroids = pg.vector_to_points(data1, pointtype="centroid")
##centroids.save("test_files/country_centroids.shp")
##
##print "to points, vertexes"
##vertexes = pg.vector_to_points(data1, pointtype="centroid")
##vertexes.save("test_files/country_vertexes.shp")
##
### to lines
##print "to lines"
##lines = pg.vector_to_lines(data1)
##lines.save("test_files/country_lines.shp")
##
### to polygons
##print "to poly, convex"
##convexes = pg.vector_to_polygons(data1, polytype="convex hull")
##convexes.save("test_files/country_convexes.shp")
##
##print "to poly, triangulate"
##triangles = pg.vector_to_polygons(centroids, polytype="delauney triangles")
##triangles.save("test_files/country_triangles.shp")
##
##print "to poly, voronoi"
##many = pg.GeoTable("test_files/shp/domestic.shp")
##triangles = pg.vector_to_polygons(many, polytype="voronoi polygons")
##triangles.save("test_files/country_voronoi.shp")
##
##print "to poly, enclose lines"
##enclosed = pg.vector_to_polygons(lines, polytype="enclose lines")
##enclosed.save("test_files/country_enclosed.shp")
##
##
##fdssdfsd
##
### merging
##print "merging"
##merged = pg.vector_merge(data1, data2)
##print len(merged)   
##
### splitting
##print "splitting"
##country_files = pg.vector_split(data1, ["CNTRY_NAME"])
##seen = []
##for country in country_files:
##    if country[1]["CNTRY_NAME"] in seen:
##        print country[1]["CNTRY_NAME"]
##        raise Exception()
##    seen.append(country[1]["CNTRY_NAME"])
##print len(seen)
##
### cleaning
##print "cleaning"
##cleaned = pg.vector_clean(data1)
##print len(cleaned)
##cleaned.save("C:/Users/BIGKIMO/Desktop/cleaned.json")
##
##print ""

###############
# RASTER DATA
###############

print "RASTER TESTS"

print "resampling"
raster = pg.Raster("test_files/geotiff/TrueMarble.16km.2700x1350.tif")
resampled = pg.raster.manager.resample(raster,
                                        cellwidth=1,
                                        cellheight=1)
#resampled.save("test_files/geotiff/bluemarb_resampled.tif")
print resampled.width, resampled.height

# trade diffs
raster1 = pg.Raster("test_files/geotiff/as_anthrome.tif")
raster2 = pg.Raster("test_files/geotiff/eu_anthrome.tif")
mosaiced = pg.raster.manager.mosaic(raster1, raster2)

##print "from vector"
##vector = pg.GeoTable("test_files/shp/cshapes.shp")
##raster = pg.raster.manager.from_vector(vector, 0.5, 0.5)




