
import pythongis as pg

d = pg.VectorData(r"C:\Users\kimok\Downloads\ne_10m_admin_1_states_provinces (1)\ne_10m_admin_1_states_provinces.shp")
d.create_spatial_index('rtree')

for e in d.quick_overlap((0,0,20,20)):
    print e

