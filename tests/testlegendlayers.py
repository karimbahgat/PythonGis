
import pythongis as pg
import math

countries = pg.VectorData("data/ne_10m_admin_0_countries.shp", encoding='latin')
points = pg.VectorData("data/ne_10m_populated_places_simple.shp", encoding='latin')

mapp = pg.renderer.Map()
mapp.add_layer(countries, fillcolor='green', legend=False)
mapp.add_layer(points, fillsize=dict(breaks='proportional', key='pop_max', sizes=[0.05,9]), fillcolor='yellow')
mapp.add_legend()
mapp.view()



