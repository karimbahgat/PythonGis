
import pythongis as pg

poly = pg.VectorData("data/ne_10m_admin_0_countries.shp")

def diagonal_left(width, height):
    import pyagg
    c = pyagg.Canvas(width, height)
    for frac in range(0,100+1,10):
        frac = frac/100.0
        x = width*frac
        y = height*frac
        c.draw_line([(x,0),(0,y)], fillcolor='black', outlinecolor=None)
        c.draw_line([(x,height),(width,y)], fillcolor='black', outlinecolor=None)
    return c

diagonal_left(1000,1000).view()
dsfsd

mapp = pg.renderer.Map(1000,500,background=None) #,background=(255,0,0))
lyr = mapp.add_layer(poly, fillcolor=filleffect)
mapp.view()




