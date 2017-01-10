
import pythongis as pg


###
print("\n"+"raster test")
rast = pg.RasterData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\geotiff\TrueMarble.16km.2700x1350.tif")
for b in rast.bands:
    #continue
    #b.img.show()#view(1000,500)
    #jlkj
    b.nodataval = 0
    #b.mask.show()#view(1000,500)
#rast.bands.pop(-1)
print rast.bands
rast.mask.show()
#rast.mask = rast.bands[0].conditional("val < 111").img
#rast.view(1000,500, type="colorscale", gradcolors=[(0,0,255),(0,255,0),(255,0,0)])
#iyiy


###
print("\n"+"multimap test")
mapp = pg.renderer.Map()
vect = pg.vector.data.VectorData(r"C:\Users\kimo\Dropbox\Work\Workplace\Geobook15\pygeo book 2\code\(raw sandbox,incl abondoned ideas)\test_files\shp\domestic.shp")
print vect.fields

mapp.add_layer(rast)  
mapp.add_layer(vect,
            fillsize={"breaks":"headtail",
                        "key":lambda f: float(f["Average_nk"]),
                        "symbolvalues":[0.2, 2.0]
                      },
            fillcolor={"breaks":"headtail",
                        "key":lambda f: float(f["Average_nk"]),
                        "symbolvalues":["blue","green","red"],
                       },
            sortkey=lambda f: float(f["Average_nk"]),
            sortorder="incr"
            )
mapp.view()
