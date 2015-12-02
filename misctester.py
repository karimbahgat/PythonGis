
import pythongis as pg

vect = pg.vector.data.VectorData(r"C:\Users\kimo\Documents\GitHub\pShapes\BaseData\ne_10m_admin_1_states_provinces.shp",
                                 encoding="latin")
print str(vect.features)[:100]
vect.features = dict([(i,f) for i,f in vect.features.items()
                      if f["geonunit"]=="Syria"])  #filter(lambda f: f.row["geounit"]=="Syria", vect.features.values())
print vect.features

##rast = pg.raster.manager.rasterize(vect, 0.1, 0.1)
##print rast

inp = pg.raster.data.RasterData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\geotiff\TrueMarble.16km.2700x1350.tif")
clipped = pg.raster.manager.clip(inp, vect)
print clipped
