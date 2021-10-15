
import pythongis as pg

d = pg.VectorData('data/ne_10m_admin_0_countries.shp')

# using the pyagg canvas defaults
m = pg.renderer.Map()
m.add_layer(d, text=lambda f: f['NAME'])
m.view()

# setting another textoptions for entire map
m = pg.renderer.Map(title='This is the Title',
                    textoptions={'font':'garamond', 'textsize':6})
m.add_layer(d, text=lambda f: f['NAME'], legendoptions={'title':'Countries'})
m.add_legend()
m.view()

# override just the title options
m = pg.renderer.Map(title='Overriding the Title Textoptions',
                    titleoptions={'font':'Segoe UI'},
                    textoptions={'font':'garamond', 'textsize':6})
m.add_layer(d, text=lambda f: f['NAME'], legendoptions={'title':'Countries'})
m.add_legend(legendoptions={'title':'Legend','titleoptions':{'font':'Times New Roman'}})
m.view()
