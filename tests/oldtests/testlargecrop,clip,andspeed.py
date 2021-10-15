
import pythongis as pg
import gc

countries = pg.VectorData("data/ne_10m_admin_0_countries.shp")
print countries

def load_agerast(country, fromage, toage, gender, year):
    agestring = format(fromage, "02") + format(toage, "02")
    name = next((f['ISO1AL3'] for f in country))
    region = {'AFG':'Asia','COL':'LAC','COD':'AFR','NGA':'AFR','YEM':'Asia'}[name]
    version = {'AFR':5,'Asia':2,'LAC':1}[region]
    filename = "{region}_PPP_A{agestring}_{gender}_{year}_adj_v{version}.tif".format(agestring=agestring,
                                                                             gender=gender,
                                                                             year=year,
                                                                             region=region,
                                                                             version=version)
    print 'loading'
    rast = pg.RasterData('data/'+filename)
    print rast.filepath
    print 'clipping'
    clip = rast.manage.clip(country, bbox=country.bbox)
    print 'cleaning'
    del rast
    gc.collect()
    return clip

def make_childrast(country, year):
    xmin,ymin,xmax,ymax = country.bbox
    calcrast = pg.RasterData(mode='float32', bbox=[xmin,ymax,xmax,ymin], #xoffset=country.bbox[0], yoffset=country.bbox[3],
                            xscale=0.00833333329999305, yscale=-0.00833333329999305)
    calcband = calcrast.add_band()
    for gend in "FM":
        print gend
        for toage in [4,9,14,19]:
            fromage = toage - 4
            print fromage,toage

            rast = load_agerast(country, fromage, toage, gend, year)
            print rast.bands[0].summarystats()
            rast.view(cutoff=(0,2))
            
            print 'summing'
            if toage == 19:
                calcband += rast.bands[0] * (3/5.0) # in agegroup 15-19, we only want 15-17, which is only 3 of the 5 years
            else:
                calcband += rast.bands[0]

    calcrast.bands[0] = calcband
    return calcrast
    

# mapit
rast = pg.RasterData(r'C:\Users\kimok\Downloads\F182013.v4c_web.stable_lights.avg_vis.tif')
#rast = pg.RasterData(r'C:\Users\kimok\Downloads\SVDNB_npp_20170701-20170731_75N060W_vcmcfg_v10_c201708061230.avg_rade9.tif')
print rast, rast.bands[0].summarystats()

rast.view(minval=0, maxval=63)
dfsd

for iso in ['NGA','COD','YEM']:
    print iso
    c = countries.select(lambda f: f["ISO_A3"]==iso)
    clip = rast.manage.clip(c, bbox=c.bbox)
    print clip
    clip.view()#cutoff=(0,10))

import gc
for t in rast.manage.tiled():#tilesize=(1000,1000)):
    print 't',t
    #print t.bands[0].summarystats()
    #t.view()
    del t
    gc.collect()

    
fsafas

##rast = pg.RasterData('data/AFR_PPP_A0004_F_2000_adj_v5.tif')
##print rast
##for t in rast.manage.tiled():#tilesize=(3000,3000)):
##    print t
##fsafas

for iso in ["AFG","COL","COD","NGA","YEM"]:
    print iso
    c = countries.select(lambda f: f["ISO_A3"]==iso)

    # age data
    childrast = make_childrast(c, 2015)
    print childrast
    print childrast.bands[0].summarystats()

print 'finished!'



