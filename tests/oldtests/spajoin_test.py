import pythongis as pg
from time import time

poly = pg.VectorData("data/ne_10m_admin_1_states_provinces.shp", encoding="latin")
points = pg.VectorData("data/ne_10m_populated_places_simple.shp", encoding="latin")
print points

##t=time()
##join = points.manage.spatial_join(points, "distance",
##                                  radius=10, n=3, # 3 nearest within 10k
##                                  key=lambda f1,f2: f1.geometry != f2.geometry) # not self
##print time()-t, join

t=time()
join = poly.manage.spatial_join(points, "intersects", clip=lambda f1,f2: f2.geometry) # poly contains points
print "fast join country to each point", time()-t, join

# HEAVY ONES

# Slow point-poly

##t=time()
##join = points.manage.spatial_join(poly, "intersects") # point in polys
##print time()-t, join

t=time()
join = points.manage.spatial_join(poly, "distance", radius=60, n=1) 
print "slow join closest country to point, within limit,", time()-t, join

t=time()
join = points.manage.spatial_join(poly, "distance", radius=60)
print "slow join all countries to point, within limit,", time()-t, join

t=time()
join = points.manage.spatial_join(poly, "distance", n=1)
print "slow join closest country to point, no limit,", time()-t, join



