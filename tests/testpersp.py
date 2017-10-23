
import pythongis as pg

W = 2000
H = 1000
SPACING = 330
RIGHTSPIN = 500
DOWNTILT = 700

c = pg.VectorData("ch est/data/cshapes.shp")

import PIL, PIL.Image

def tilt(img, oldplane, newplane):
    pb,pa = oldplane,newplane
    grid = []
    for p1,p2 in zip(pa, pb):
        grid.append([p1[0], p1[1], 1, 0, 0, 0, -p2[0]*p1[0], -p2[0]*p1[1]])
        grid.append([0, 0, 0, p1[0], p1[1], 1, -p2[1]*p1[0], -p2[1]*p1[1]])
    import advmatrix as mt
    A = mt.Matrix(grid)
    B = mt.Vec([xory for xy in pb for xory in xy])
    AT = A.tr()
    ATA = AT.mmul(A)
    gridinv = ATA.inverse()
    invAT = gridinv.mmul(AT)
    res = invAT.mmul(B)
    transcoeff = res.flatten()
    #then calculate new coords, thanks to http://math.stackexchange.com/questions/413860/is-perspective-transform-affine-if-it-is-why-its-impossible-to-perspective-a"
    new = img.transform(img.size, PIL.Image.PERSPECTIVE, transcoeff, PIL.Image.BILINEAR)
    return new

oldplane = [ (0,0), (W,0), (W,H), (0, H) ]
#newplane = [ (600,500), (1200,500), (W,H), (0, H) ]
#newplane = [ (0+500,0+700), (W,0+700), (W-500,H), (0, H) ]
#newplane = [ (0+700,0), (W,0+400), (W-700,H), (0, H-400) ]
#newplane = [ (0+700,0), (W,0+800), (W-700,H), (0, H-800) ]
newplane = [ (0+RIGHTSPIN,0+DOWNTILT), (W,0+DOWNTILT), (W-RIGHTSPIN,H), (0, H) ]

out = PIL.Image.new("RGBA", (W,H), 0)
lyr = tilt(c.render(W,H,background="white").img, oldplane, newplane)
out.paste(lyr, (0,0), mask=lyr)
lyr = tilt(c.render(W,H,background="white").img, oldplane, newplane)
out.paste(lyr, (0,-SPACING), mask=lyr)
lyr = tilt(c.render(W,H,background="white").img, oldplane, newplane)
out.paste(lyr, (0,-SPACING*2), mask=lyr)
out.show()
