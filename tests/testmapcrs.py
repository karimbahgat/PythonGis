
import pythongis as pg
import pycrs

pg.vector.data.DEFAULT_SPATIAL_INDEX = 'quadtree'

data = pg.VectorData(r"C:\Users\kimok\Desktop\BIGDATA\priocountries\priocountries.shp")
rast = pg.RasterData(r"C:\Users\kimok\OneDrive\Documents\GitHub\AutoMap\tests\testmaps\burkina_georeferenced.tif")

#testcrs = '+proj=robin +datum=WGS84 +ellps=WGS84 +a=6378137.0 +rf=298.257223563 +pm=0 +lon_0=0 +x_0=0 +y_0=0 +units=m +axis=enu +no_defs'
#testcrs = pycrs.parse.from_sr_code(6980).to_proj4() # space
#testcrs = pycrs.parse.from_sr_code(7619).to_proj4() # goode?
#testcrs = next(pycrs.utils.search('van der grinten'))['proj4']
testcrs = next(pycrs.utils.search('eckert iv'))['proj4']




#### original crs
#data.view()

#### test on-the-fly crs
#data.view(crs=testcrs)

#### raster crs
rast.view() #testcrs)
#rast.manage.reproject(testcrs, resample='nearest').view()
#rast.manage.reproject(testcrs, resample='bilinear').view()

dsadsads




#### multiple different crs on same map
m = pg.renderer.Map(width=1000,height=500,crs=testcrs)

# water background in longlat
water = pg.VectorData()
geoj = {'type':'Polygon', 'coordinates':[[(x,y) for x in range(-180,180+1,1) for y in range(-90,90+1,1)]]}
water.add_feature([], geoj)
lyr = m.add_layer(water, fillcolor='skyblue', outlinecolor=None)

# countries in mollweide
tocrs = next(pycrs.utils.search_name('mollweide'))['proj4']
dataproj = data.manage.reproject(tocrs)
dataproj.crs = tocrs
#dataproj.view()
lyr = m.add_layer(dataproj, fillcolor='darkgreen')

# rivers in eckert iv
rivers = pg.VectorData(r"C:\Users\kimok\Desktop\BIGDATA\testup\Natural Earth, rivers\ne_10m_rivers_lake_centerlines.shp")
tocrs = next(pycrs.utils.search_name('eckert IV'))['proj4']
rivers = rivers.manage.reproject(tocrs)
rivers.crs = tocrs
#rivers.view()
lyr = m.add_layer(rivers, fillcolor='blue', fillsize='0.3px', outlinecolor=None)

m.zoom_auto()
#m.save('C:/Users/kimok/Desktop/testmap.png', meta=True)
m.view()






fasdfadfa






########################

# random play with nice map
m = pg.renderer.Map(width=1000,height=500,crs=testcrs,background='black')

water = pg.VectorData()
geoj = {'type':'Polygon', 'coordinates':[[(x,y) for x in range(-180,180+1,1) for y in range(-90,90+1,1)]]}
water.add_feature([], geoj)
lyr = m.add_layer(water, fillcolor='blue', outlinecolor=None)
lyr.add_effect('glow',
               color=[(255,255,255,255),(255,255,255,0)],
               size=30)
##lyr.add_effect('glow',
##               color=(255,255,255), #[(255,255,255,255),(255,255,255,0)],
##               size=30)
##lyr.add_effect('inner',
##               color=(255,0,0), #[(255,255,255,255),(255,255,255,0)],
##               size=3)
##lyr.add_effect('shadow',
##               xdist=30, ydist=30)

lyr = m.add_layer(data, fillcolor='darkgreen', outlinecolor='gray')
m.zoom_auto()
m.view()





#######################

# random create projection icon
crs = next(pycrs.utils.search('mercator'))['proj4']
m = pg.renderer.Map(width=500,height=500,crs=crs)

lyr = m.add_layer(data, fillcolor='black')

gridlines = pg.VectorData()
horiz = [[(x,y) for x in range(-180,180+1,1)] for y in range(-90,90+1,30)]
vertic = [[(x,y) for y in range(-90,90+1,1)] for x in range(-180,180+1,60)]
geoj = {'type':'MultiLineString', 'coordinates':horiz+vertic}
gridlines.add_feature([], geoj)
lyr = m.add_layer(gridlines, fillcolor='black', fillsize=1, outlinecolor=None)

m.save(r'C:\Users\kimok\OneDrive\Documents\GitHub\PythonGis\pythongis\app\icons\projections.png')
from PIL import ImageOps
im = m.img
im = ImageOps.expand(im, 10, (0,0,0))
im.show()
im = ImageOps.expand(im, 50, (255,255,255,0))
im.save(r'C:\Users\kimok\OneDrive\Documents\GitHub\PythonGis\pythongis\app\icons\projections.png')
m.view()


