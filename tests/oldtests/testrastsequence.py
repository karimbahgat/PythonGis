
import pythongis as pg
import gc

# create the test data
##focus = pg.VectorData("data/ne_10m_admin_0_countries.shp", select=lambda f: f['ISO_A3']=='IRN')
##print focus
##for yr in [1990,2000,2015]:
##    rast = pg.RasterData(r"C:\Users\kimok\Desktop\redd barna\Input\pop%s.tif"%yr)
##    clip = rast.manage.clip(focus, bbox=focus.bbox)
##    print clip
##    clip.save('data/pop%s.tif'%yr)

for yr,rast in pg.raster.manager.sequence(range(1990,2015+1),
                                          rasts={1990: lambda: pg.RasterData(r'data/pop1990.tif'),
                                                2000: lambda: pg.RasterData(r'data/pop2000.tif'),
                                                2015: lambda: pg.RasterData(r'data/pop2015.tif')
                                                 }):
    print yr
    #print rast.bands[0].summarystats()
    #rast.view()







