
import pythongis as pg
from random import randrange

def catmullrom(y0,y1,y2,y3,mu):
    "http://paulbourke.net/miscellaneous/interpolation/"
    mu2 = mu*mu
    a0 = -0.5*y0 + 1.5*y1 - 1.5*y2 + 0.5*y3
    a1 = y0 - 2.5*y1 + 2*y2 - 0.5*y3
    a2 = -0.5*y0 + 0.5*y2
    a3 = y1
    return a0*mu*mu2+a1*mu2+a2*mu+a3

mapp = pg.renderer.Map()

points = pg.VectorData()
for x in range(-180,180,10):
    y = randrange(-90,90)
    points.add_feature(geometry={'type':'Point','coordinates':(x,y)})

# smaller step size (below) makes it finer,
# bigger generalizes (but only between the selected sample/fraction points,
# for true generelizing have to aggregate to coarser resolution,
# then interpolate between)
lines = pg.VectorData()
line = []
for x in range(-180,180,1): 
    frac = (x+180) / 360.0
    pos = len(points)*frac + 1 # +1 only cus features is 1-based
    try: p0,p1,p2,p3 = points[int(pos)-1],points[int(pos)],points[int(pos)+1],points[int(pos)+2]
    except KeyError: continue
    mu = pos - int(pos)
    y0,y1,y2,y3 = [p.geometry['coordinates'][1] for p in (p0,p1,p2,p3)]
    #print x,frac,pos,p1.geometry['coordinates'],mu
    y = catmullrom(y0,y1,y2,y3,mu)
    line.append((x,y))
lines.add_feature(geometry={'type':'LineString','coordinates':line})

mapp.add_layer(points)
mapp.add_layer(lines, fillsize='0.1mm', outlinewidth=0)
mapp.view()
