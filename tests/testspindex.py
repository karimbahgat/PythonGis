
import pythongis as pg
from random import uniform

def test_rtree_init(backend, **kwargs):
    spindex = pg.vector.spindex.Rtree(backend=backend, **kwargs)
    print('init',spindex)
    return spindex

def test_quadtree_init(backend, **kwargs):
    spindex = pg.vector.spindex.QuadTree(backend=backend, **kwargs)
    print('init',spindex)
    return spindex
        
def test_build(spindex):
    for i,(x,y) in boxes:
        spindex.insert(i, [x,y,x+1,y+1])
    print('built')

def test_matches(spindex, matchbox):
    matches = list(spindex.intersects(matchbox))
    print('matches', len(matches))

################

d = pg.VectorData('data/ne_10m_admin_0_countries.shp')
matchbox = [1,1,20,20]

d.create_spatial_index()
print('default',d.spindex)

pg.vector.data.DEFAULT_SPATIAL_INDEX = 'rtree'
d.create_spatial_index()
print('default rtree',d.spindex)
print(len(list(d.quick_overlap(matchbox))))

pg.vector.data.DEFAULT_SPATIAL_INDEX = 'quadtree'
d.create_spatial_index()
print('default quadtree',d.spindex)
print(len(list(d.quick_overlap(matchbox))))

d.create_spatial_index('rtree')
print('specify rtree',d.spindex)
print(len(list(d.quick_overlap(matchbox))))

d.create_spatial_index('quadtree')
print('specify quadtree',d.spindex)
print(len(list(d.quick_overlap(matchbox))))

################

n = 10000
boxes = [(i, (uniform(-180,180),uniform(-90,90)) ) for i in range(n)]
matchbox = [1,1,20,20]

print('rtree')
spindex = test_rtree_init(None)
test_build(spindex)
test_matches(spindex, matchbox)

print('rtree, rtree backend')
spindex = test_rtree_init('rtree')
test_build(spindex)
test_matches(spindex, matchbox)

print('rtree, pyrtree backend')
spindex = test_rtree_init('pyrtree')
test_build(spindex)
test_matches(spindex, matchbox)

print('quadtree')
spindex = test_quadtree_init(None, bbox=[-180,-90,180,90])
test_build(spindex)
test_matches(spindex, matchbox)

print('quadtree, pyqtree backend')
spindex = test_quadtree_init('pyqtree', bbox=[-180,-90,180,90])
test_build(spindex)
test_matches(spindex, matchbox)


