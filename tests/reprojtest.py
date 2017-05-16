
import pythongis as pg

data = pg.VectorData(r"C:\Users\kimo\Downloads\cshapes_0.6\cshapes.shp",
                     ) #select=lambda f: f["GWSYEAR"] == 1990)

# vector
##proj = data.manage.reproject("+proj=latlong +datum=WGS84",
##                             "+proj=robin +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
##
##proj.bbox
##
##proj.view()

# raster

rast = pg.raster.manager.rasterize(data, bbox=[-170,80,170,-80], width=720, height=360)
#rast.view()

rast.crs = "+proj=latlong +datum=WGS84"
reproj = pg.raster.manager.reproject(rast, "+proj=robin +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
reproj.view()
