
import shapefile_stream as pyshp

# write
##w = pyshp.Writer(pyshp.POINT)
##w.field("hello")
##for _ in range(10000):
##    w.point(5,5)
##    w.record("world")
##w.save("bigfile.shp")
##print "saved"

w = pyshp.Writer(pyshp.POLYGON)
r = pyshp.Reader(r"C:\Users\kimo\Downloads\ne_10m_admin_1_states_provinces\ne_10m_admin_1_states_provinces.shp")
w.field("hello")
##for f in r.fields:
##    w.field(*f)
for _ in range(5):
    print _
    for f in r.iterShapeRecords():
        #print f.record
        #w.record(*f.record)
        w.record("world")
        
        #w._shapes.append(f.shape)
        w.shape(f.shape)
w.save("bigfile.shp")
print "saved"

# read back
##r = pyshp.Reader("bigfile.shp")
##print r, r.numRecords
##for _ in r.iterShapeRecords():
##    pass
##print "read"

##import pythongis as pg
##pg.VectorData("bigfile.shp").view()


