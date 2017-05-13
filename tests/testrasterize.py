
import pythongis as pg
from time import time



# conflictsite
confs = pg.VectorData("C:/Users/kimo/Downloads/Conflict Site Dataset 2.0/Conflict Site 4-2006.xls",
                    xfield="Longitude", yfield="Latitude")
print confs, confs.fields
confs = confs.manage.buffer(lambda f: f["Radius"], geodetic=True)

countries = pg.VectorData("C:/Users/kimo/Downloads/cshapes_0.6/cshapes.shp")
countries = countries.select(lambda f: f["GWCODE"]!=-1)

# clip to countries
##for f in confs:
##    print f
##    relevant = [gw for gw in countries if str(gw["GWCODE"]) in f["Conflict site"].split(", ")]
##    for 
##        :
##            f.geometry = f.get_shapely().intersection(gw.get_shapely())
##confs.view()

deaths = pg.VectorData("C:/Users/kimo/Downloads/PRIO Battle Deaths Dataset 3.1.xls")
print deaths.fields
confs = confs.join(deaths, (lambda f: (f["ID"],f["Year"]), lambda f: (f["id"],f["year"])))
confs = confs.select(lambda f: isinstance(f["bdeadbes"],float) and f["bdeadbes"] >= 0)

# distribute based on area covered
def area_weighted(cell, feat):
    isec = feat._shapely.intersection(cell)
    w = isec.area / feat._shapely.area
    return w

t = time()
rast = pg.raster.manager.rasterize(confs,
                                   valuekey=lambda f: f["bdeadbes"],
                                   #weight=area_weighted,
                                   stat="sum",
                                   bbox=[-180,90,180,-90], width=720, height=360)
print time()-t, "secs"
rast.view()

fsdfdss

# distribute based on underlaying population
# allocate function:
# clip pop rast to feat
# calc total pop
# weight deaths by cell's pop share of total pop
# this way, each feat's deaths is distributed perfectly based on pop distribution








# load cshapes
vec = pg.VectorData("C:/Users/kimo/Downloads/cshapes_0.6/cshapes.shp")
vec = vec.select(lambda f: f["GWEYEAR"]==2016) # and f["CNTRY_NAME"]<"D") #f["CNTRY_NAME"]!="Canada") # and f["CNTRY_NAME"]<"C")

# gwno allocation
t = time()
def largest(cell,feats):
    if len(feats) > 1:
        return sorted(feats, key=lambda f: f._shapely.intersection(cell).area)
    else:
        return feats
def largest_over(cell,feats):
    areas = [(f, f._shapely.intersection(cell).area) for f in feats]
    carea = cell.area
    over = [(f,a) for f,a in areas if a >= carea/2.0] # over 50% cell area
    return [f for f,a in sorted(over, key=lambda(f,a): a)]

gwno = pg.raster.manager.rasterize(vec,
                                   valuekey=lambda f: f["GWCODE"],
                                   choose=largest,
                                   stat="last",
                                   bbox=[-180,90,180,-90], width=720, height=360)
print time()-t,"secs"

mapp = pg.renderer.Map()
mapp.add_layer(gwno)
mapp.add_layer(vec)
mapp.view()

# overlap count
overlap = pg.raster.manager.rasterize(vec,
                                   valuekey=lambda f: 1,
                                   stat="sum",
                                   bbox=[-180,90,180,-90], width=72, height=36)
overlap.view()
