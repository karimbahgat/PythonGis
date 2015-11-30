
import time, os

import pythongis as pg

def runtests(filepath):

    print "------------"
    print filepath
    
    # basic
    t = time.time()
    raster = pg.Raster(filepath)
    print "loaded",raster
    print time.time()-t

    print raster.info

    for band in raster:
        print "---"
        #band.img.show()
        print band.img.getextrema()
        print band.img.size
        print band.cells
        print band.img.mode
        print band.get(44,44)
        print band.get(44,44).neighbours

testfiles = ["test_files/geotiff/TrueMarble.16km.2700x1350.tif",
             "test_files/ascii/rain_california.asc",
             "test_files/ascii/testraster.asc"]

for testfile in testfiles:
    runtests(testfile)

print "done"
