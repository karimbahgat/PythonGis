
import time, os

import pythongis as pg

def runtests(filepath):

    print "------------"
    print filepath
    
    # basic
    t = time.time()
    geofile = pg.GeoTable(filepath)
    print "loaded",geofile
    print time.time()-t

    print "fields",geofile.fields

    t = time.time()
    print "bbox",geofile.bbox
    print time.time()-t

    t = time.time()
    geofile.create_spatial_index()
    print "spindex"
    print time.time()-t

    print len(geofile)
    print "custom"
    for feat in geofile.quick_overlap([-30/4,-15/4,30/4,15/4]):
        print feat.row[0], feat.bbox
    print "ne", len(list(geofile.quick_overlap([0,0,180,90])))
    print "se", len(list(geofile.quick_overlap([0,-90,180,0])))
    print "sw", len(list(geofile.quick_overlap([-180,-90,0,0])))
    print "nw", len(list(geofile.quick_overlap([-180,0,0,90])))
    
    for feat in geofile:
        print feat.id
        print feat.row
        print feat.bbox
        print "..."
        break

    geofile.save("testsave.shp")
    os.remove("testsave.shp")
    os.remove("testsave.dbf")
    os.remove("testsave.shx")

testfiles = ["test_files/gpx/%s"%filename
             for filename in os.listdir("test_files/gpx/")]
##testfiles = ["test_files/shp/cshapes.shp",
##         "test_files/geoj/cshapes.geo.json",
##         "test_files/gpx/korita-zbevnica.gpx"]

for testfile in testfiles:
    try: runtests(testfile)
    except Exception as errmsg: print errmsg

print "done"
