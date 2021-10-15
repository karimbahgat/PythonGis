
import gdal
import pythongis as pg

rast = gdal.Open(r'C:\Users\kimok\Desktop\nhsce_v01r01_19661004_20171106.nc')

lats = gdal.Open(rast.GetSubDatasets()[0][0], gdal.GA_ReadOnly).ReadAsArray()
lons = gdal.Open(rast.GetSubDatasets()[1][0], gdal.GA_ReadOnly).ReadAsArray()
vals = gdal.Open(rast.GetSubDatasets()[-1][0], gdal.GA_ReadOnly).ReadAsArray()
bbox = [-180,90,180,0] #[lons.min(), lats.min(), lons.max(), lats.max()]
print bbox

time = 0 # startweek is oct. +3mn is end of dec

# raw lat lon
d = pg.VectorData(fields=['col','row','i'])
for col in range(88):
    #print col
    for row in range(88):
        i = col*row + row
        lat,lon = lats[row,col], lons[row,col]
        val = vals[time,row,col]
        if val==0: continue
        #print lat,lon
        d.add_feature(row=[col,row,i],geometry={'type':'Point','coordinates':(lon,lat)})

d.view(fillcolor=dict(breaks='proportional',key='i'))
dvec = d

# raw grid
data = [v for r in vals[time] for v in r]
import PIL,PIL.Image
img = PIL.Image.new('L', (88,88))
img.putdata(data)
d = pg.RasterData(image=img, width=88, height=88, bbox=[0,0,1,1])
d.view()

# projected stereo
import pyproj
stereo = pyproj.Proj(init='EPSG:3411')
d = pg.VectorData(fields=['col','row','i','val'])
for col in range(88):
    #print col
    for row in range(88):
        i = col*row + row
        lat,lon = lats[row,col], lons[row,col]
        val = vals[time,row,col]
        if val == 0: continue
        #print lat,lon
        x,y = stereo(lon,lat)
        d.add_feature(row=[col,row,i,val],geometry={'type':'Point','coordinates':(x,y)})

d.view(fillcolor=dict(breaks='proportional',key='i', colors=['blue','yellow']))
sdvec = d

# store as grid with stereo coordsys

#bbox = [lons[0][0], lats[0][0], lons[-1][-1], lats[-1][-1]]
##bbox = stereo(*bbox[:2]) + stereo(*bbox[2:])
##print bbox
##d = pg.RasterData(mode='float32', width=88, height=88, bbox=bbox)
##b = d.add_band()
##time = 4*3
##for c in b:
##    row,col = c.row,c.col
##    val = vals[time,row,col]
##    b.set(col,row,val)
##d.view()

# define coordsys via stereo coords bbox
# SAMPLES CORRECTLY! but does not account for the affine rotation...
# BEST IDEA:
# do this by finding 2-3 tiepoints bw grid coords and crs coords, and computing affine
# https://stackoverflow.com/questions/22954239/given-three-points-compute-affine-transformation
# OTHER:
# https://elonen.iki.fi/code/misc-notes/affine-fit/
# https://stackoverflow.com/questions/11687281/transformation-between-two-set-of-points
# https://gis.stackexchange.com/questions/63107/using-proj-4-library-to-transform-from-local-coordinate-system-coordinates-to-gl
# http://www.perrygeo.com/python-affine-transforms.html
lonlats = zip([l for sub in lons for l in sub], [l for sub in lats for l in sub])
slonlats = [stereo(lon,lat) for lon,lat in lonlats]
slons,slats = zip(*slonlats)
bbox = min(slons),max(slats),max(slons),min(slats)
#bbox = stereo(-180,0) + stereo(180,90) 
print bbox

d = pg.RasterData(mode='float32', width=88, height=88, bbox=bbox)
b = d.add_band()
for c in b:
    # OLD
##    row,col = c.row,c.col
##    lat,lon = lats[row,col], lons[row,col]
##    x,y = stereo(lon,lat)
##    val = vals[time,row,col]
##    try:d.set(x,y,val,0)
##    except:pass
    
    # NEW
    x,y = c.x,c.y
    col,row = d.geo_to_cell(x,y)
    val = vals[time,row,col]
    try: c.value = val
    except: pass
d.view()

mapp = pg.renderer.Map()
mapp.add_layer(d)
mapp.add_layer(sdvec)
mapp.add_layer('data/ne_10m_admin_0_countries.shp', fillcolor=None)
mapp.view()

# sample to desired lonlat raster
r = pg.RasterData(mode='float32', width=720, height=360, bbox=[-180,90,180,-90])
b = r.add_band()

##for col in range(88):
##    #print col
##    for row in range(88):
##        lat,lon = lats[row,col], lons[row,col]
##        val = vals[time,row,col]
##        try:r.set(lon,lat,val,0)
##        except:pass

for c in b:
    lon,lat = c.x, c.y
    x,y = stereo(lon,lat)
    #print lon,lat,x,y
    try:
        val = d.get(x,y,0).value
        c.value = val
    except:pass

#b.nodataval = 0
mapp = pg.renderer.Map()
mapp.add_layer(r)
mapp.add_layer(dvec)
mapp.add_layer('data/ne_10m_admin_0_countries.shp', fillcolor=None)
mapp.view()


