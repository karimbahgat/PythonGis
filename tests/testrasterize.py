
import pythongis as pg
from time import time


if 1:
    # conflictsite
    confs = pg.VectorData("C:/Users/kimo/Downloads/Conflict Site Dataset 2.0/Conflict Site 4-2006.xls",
                        xfield="Longitude", yfield="Latitude")
    print confs, confs.fields
    confs = confs.manage.buffer(lambda f: f["Radius"], geodetic=True, resolution=20)
    #confs.view()

    countries = pg.VectorData("C:/Users/kimo/Downloads/cshapes_0.6/cshapes.shp")
    countries = countries.select(lambda f: f["GWCODE"]!=-1)

    # clip to countries (hacky for now, what happened to the intersection method?) 
    from shapely.ops import cascaded_union
    for f in confs:
        print ["vector intersecting",f,f.id,len(confs)]
        fg = f.get_shapely()
        intsecs = [fg.intersection(gw.get_shapely())
                       for gw in countries
                       if gw["GWSYEAR"] <= f["Year"] <= gw["GWEYEAR"] \
                       and int(float(gw["GWCODE"])) in [int(float(cod)) for cod in str(f["Conflict site"]).split(",")]]
        if len(intsecs) == 1:
            newg = intsecs[0].__geo_interface__
        elif len(intsecs) > 1:
            newg = cascaded_union(intsecs).__geo_interface__
        else: 
            continue # no gw match
        f.geometry = newg if "coordinates" in newg else None # excludes weird geomcollection intersection results
    confs = confs.select(lambda f: f.geometry)
    #confs.view()

    deaths = pg.VectorData("C:/Users/kimo/Downloads/PRIO Battle Deaths Dataset 3.1.xls")
    print deaths.fields
    confs = confs.join(deaths, (lambda f: (f["ID"],f["Year"]), lambda f: (f["id"],f["year"])))
    confs = confs.select(lambda f: isinstance(f["bdeadbes"],float) and f["bdeadbes"] >= 0)

    # area standardize deaths
    confs.compute("bdeadbes", lambda f: f["bdeadbes"] / f.get_shapely().area)

    # distribute based on area covered
    # TODO: WEIGHT NOT YET SUPPORTED, NEED CLEVER FLEXIBLE SOLUTION
    # MAYBE:
    # partial=only applied to borders
    # choose=only applied to overlapping
    # filter=filter any...
    # transform=transform any value...
    # borderpass (filter,transform,partial)
    # overlappass (filter,transform,choose)
    def sum_area_weighted(cell, feats):
        def isecs():
            for feat in feats:
                isec = feat._shapely.intersection(cell)
                w = isec.area / cell.area
                val = feat["bdeadbes"] * w
                yield val,isec,feat

        vals = (val for val,isec,feat in isecs())
        return sum(vals)

    t = time()
    rast = pg.raster.manager.rasterize(confs,
                                       valuekey=lambda f: f["bdeadbes"],
                                       overlap=sum_area_weighted,
                                       bbox=[-180,90,180,-90], width=720, height=360)
    print time()-t, "secs"
    rast.view()

    fsdfdss

    # ??? 
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
        return sorted(feats, key=lambda f: f._shapely.intersection(cell).area)[-1]["GWCODE"]
    else:
        return feats[0]["GWCODE"]
    
##def largest_over(cell,feats):
##    areas = [(f, f._shapely.intersection(cell).area) for f in feats]
##    carea = cell.area
##    over = [(f,a) for f,a in areas if a >= carea/2.0] # over 50% cell area
##    return [f for f,a in sorted(over, key=lambda(f,a): a)][-1]["GWCODE"]

gwno = pg.raster.manager.rasterize(vec,
                                   valuekey=lambda f: f["GWCODE"],
                                   overlap=largest,
                                   bbox=[-180,90,180,-90], width=720, height=360)
print time()-t,"secs"

mapp = pg.renderer.Map()
mapp.add_layer(gwno)
mapp.add_layer(vec)
mapp.view()

# overlap count
overlap = pg.raster.manager.rasterize(vec,
                                   valuekey=lambda f: 1,
                                   overlap=lambda(c,fs):len(fs),
                                   bbox=[-180,90,180,-90], width=72, height=36)
overlap.view()
