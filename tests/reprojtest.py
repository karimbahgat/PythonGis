
import pythongis as pg

data = pg.VectorData("data/ne_10m_admin_0_countries.shp")
print data

# vector
proj = data.manage.reproject("+proj=latlong +datum=WGS84",
                             "+proj=robin +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs")

print proj

proj.view()

grid = pg.VectorData()
for x in range(-180,180+1,20):
    line = [[x,y] for y in range(90,-90-1,-10)]
    geoj = dict(type='LineString', coordinates=line)
    grid.add_feature(geometry=geoj)

grid = grid.manage.reproject("+proj=latlong +datum=WGS84",
                             "+proj=robin +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs")

grid.view(outlinecolor=None)

# raster

rast = pg.raster.manager.rasterize(data, bbox=[-170,80,170,-80], width=720, height=360)
#rast.view()

rast.crs = "+proj=latlong +datum=WGS84"
reproj = pg.raster.manager.reproject(rast, "+proj=robin +lon_0=0 +x_0=0 +y_0=0 +ellps=WGS84 +datum=WGS84 +units=m +no_defs")
reproj.view()
