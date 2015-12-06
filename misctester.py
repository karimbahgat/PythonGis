
import pythongis as pg


# TEST RASTERIZE
##print "\n"+"rasterize"
##vect = pg.vector.data.VectorData(r"C:\Users\kimo\Documents\GitHub\pShapes\BaseData\ne_10m_admin_1_states_provinces.shp",
##                                 encoding="latin")
##vect.features = dict([(i,f) for i,f in vect.features.items()
##                      if f["geonunit"]=="Syria"])  #filter(lambda f: f.row["geounit"]=="Syria", vect.features.values())
##print vect.features

##rast = pg.raster.manager.rasterize(vect, 0.1, 0.1)
##print rast


# TEST LOADING
print "\n"+"TEST load raster"
inp = pg.raster.data.RasterData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\geotiff\TrueMarble.16km.2700x1350.tif")
#inp = pg.raster.data.RasterData(r"C:\Users\kimo\Downloads\F101992.v4b_web.stable_lights.avg_vis.tif",
#                                bbox=[33000, 7000, 35000, 9000]) # DOESNT YET WORK CUS NOT CHANGING GEOTRANS
band1 = inp.bands[0]
print inp
print "before", band1.summarystats()


# TEST COMPUTE
print "\n"+"TEST compute"
inp.convert("F")
band1.compute("val * 2")
print inp
print band1.summarystats()


# TEST RECLASSIFY
print "\n"+"TEST reclassify"
band1.reclassify("val < 30", 111)
print band1.summarystats()

pos = inp.positioned(555,555,[-180,90,0,0])
pos.bands[0].img.show()

fdsfsdf



# old tests
##inp = pg.raster.data.RasterData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\geotiff\TrueMarble.16km.2700x1350.tif")
##clipped = pg.raster.manager.clip(inp, vect)
##print clipped
##
##print clipped.bands[0].img
##clipped.bands[0].img.save("premath.png")
##for band in clipped.bands:
##    band.img = band.img.convert("L")
##rasters = [clipped]
###calibrated = pg.raster.analyzer.math("1.5 + float(raster1) ** 1.1", rasters)
##mask = pg.raster.analyzer.math("raster1 > 100", rasters)
##for band in mask.bands:
##    band.img = band.img.convert("L")
##rasters.append(mask)
##calibrated = pg.raster.analyzer.math("int(raster1) & int(raster2)", rasters)
##print calibrated.bands[0].img.getcolors()
##calibrated.bands[0].img.convert("RGB").save("mathcalib.png")
