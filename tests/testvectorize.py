
import pythongis as pg

# load cshapes
vec = pg.VectorData("C:/Users/kimo/Downloads/cshapes_0.6/cshapes.shp")
vec = vec.select(lambda f: f["GWEYEAR"]==2016 and f["CNTRY_NAME"]<"D") #f["CNTRY_NAME"]!="Canada") # and f["CNTRY_NAME"]<"C")

# 1: binary

if 0:
    # rasterize
    rast = pg.raster.manager.rasterize(vec, bbox=[-180,90,180,-90], width=720, height=360)
    print rast
    #rast.view()

    # vectorize back
    revec = pg.raster.manager.vectorize(rast, mergecells=True)
    print revec
    revec.view()

# 1: by value

if 1:
    # rasterize
    rast = pg.raster.manager.rasterize(vec, valuekey=lambda f: f["GWCODE"], stat="first",
                                       bbox=[-180,90,180,-90], width=720, height=360)
    print rast
    rast.view()

    # vectorize back
    revec = pg.raster.manager.vectorize(rast, mergecells=True)
    print revec
    revec.view(fillcolor=dict(breaks="unique",key="value"))
