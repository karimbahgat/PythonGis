
import pythongis as pg

conf = pg.VectorData('rosling/data/ged171_excelcsv.csv', encoding='latin',
                     xfield='longitude', yfield='latitude',
                     select=lambda f: f['year']==2016)
conf.compute('dum', 1)

width = 720
height = 360

agg = pg.raster.manager.rasterize(conf, valuekey=lambda f: f['dum'], stat='sum', width=width, height=height, bbox=[-180,90,180,-90])
mapp = agg.render(cutoff=(0,100))
mapp.add_legend()
mapp.save('agg.png')

smooth = pg.raster.analyzer.smooth(conf,
                                 rasterdef=dict(mode='float32', width=width, height=height, bbox=[-180,90,180,-90]),
                                   algorithm='radial',
                                   radius=3,
                                 )
smooth.bands[0].nodataval = 0
mapp = smooth.render(cutoff=(0,100))
mapp.add_legend()
mapp.save('radial.png')

smooth = pg.raster.analyzer.smooth(conf,
                                 rasterdef=dict(mode='float32', width=width, height=height, bbox=[-180,90,180,-90]),
                                   algorithm='gauss',
                                   radius=3,
                                 )
smooth.bands[0].nodataval = 0
mapp = smooth.render(cutoff=(0,100))
mapp.add_legend()
mapp.save('gauss.png')
