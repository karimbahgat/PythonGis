
import pythongis as pg

data = pg.VectorData(r"C:\Users\kimo\Downloads\cshapes_0.6\cshapes.shp",
                     ) #select=lambda f: f["GWSYEAR"] == 1990)

proj = data.manage.reproject("+proj=latlong +datum=WGS84",
                             "+proj=robin +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs")

proj.bbox

proj.view()
