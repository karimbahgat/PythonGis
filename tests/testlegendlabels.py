
import pythongis as pg

c = pg.VectorData(r"C:\Users\kimok\Desktop\ch est\data\cshapes.shp",
                  select=lambda f: f['GWEYEAR']==2016)

# normal colors
mapp = pg.renderer.Map(4000,2000,title='World Map')
mapp.add_layer(c, fillcolor=dict(breaks='natural',
                                 key='GWCODE',
                                 colors=['green','red']))
mapp.add_legend(legendoptions=dict(title='Legend'))
mapp.save("normal color breaks.png")

# normal sizes
mapp = pg.renderer.Map(2000,1000,title='World Map')
mapp.add_layer(c.convert.to_points(), fillsize=dict(breaks='natural',
                                     key='GWCODE',
                                     sizes=[0.2,2.0]))
mapp.add_legend()
mapp.save("normal size breaks.png")

# normal multiple breaks
mapp = pg.renderer.Map(2000,1000,title='World Map')
mapp.add_layer(c.convert.to_points(),
               fillsize=dict(breaks='natural',
                                     key='GWCODE',
                                     sizes=[0.2,2.0]),
               fillcolor=dict(breaks='natural',
                                 key='GWCODE',
                                 colors=['green','red']))
mapp.add_legend()
mapp.save("normal multiple breaks.png")

# proportional colors
mapp = pg.renderer.Map(2000,1000,title='World Map')
mapp.add_layer(c,
               fillcolor=dict(breaks='proportional',
                                 key='GWCODE',
                                 colors=['green','red']),
               #legendoptions=dict(title='GWNO', labeloptions=dict(textsize=11))
               )
print mapp.layers[0].legendoptions
mapp.add_legend()
mapp.save("proportional colors.png")
