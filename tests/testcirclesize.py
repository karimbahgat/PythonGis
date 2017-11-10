
import pythongis as pg
import math

points = pg.VectorData("data/ne_10m_populated_places_simple.shp", encoding='latin')
#points.browse()

def radsize(f):
    val = f['pop_max']
    sz = round(val*2/10000000.0, 2) # weird relative dist error due to small e- nr...
    return sz

def areasize(f):
    val = f['pop_max']
    area = round(val*2/10000000.0, 2)
    sz = math.sqrt(area/math.pi)
    return sz

# custom
#points.view(fillsize=radsize, fillcolor='yellow')
#points.view(fillsize=areasize, fillcolor='yellow')

# builtin
#points.view(fillsize=dict(breaks='proportional', key='pop_max', sizes=[0.1,1]), fillcolor='yellow')
mapp = pg.renderer.Map()
mapp.add_layer(points, fillsize=dict(breaks='proportional', key='pop_max', sizes=[0.05,9]), fillcolor='yellow')
mapp.add_legend()
mapp.view()

mapp = pg.renderer.Map()
mapp.add_layer(points, fillsize=0.05, fillcolor='yellow')
mapp.add_legend()
mapp.view()


