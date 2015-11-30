
# Overview of methods
# http://gis.stackexchange.com/questions/55196/how-can-i-get-the-proj4-string-or-epsg-code-from-a-shapefile-prj-file

# For PRJ files
# http://gis.stackexchange.com/questions/7608/shapefile-prj-to-postgis-srid-lookup-table/7615#7615

# For geojson epsg codes
# https://github.com/rhattersley/pyepsg/blob/master/pyepsg.py

# Geotiff is different?
# http://trac.osgeo.org/geotiff/wiki/RefiningGeoTIFF

# Maybe based on these tables?
# http://www.remotesensing.org/geotiff/spec/geotiff2.5.html

# Maybe just hardcode support for these ones bc they explicitly translate the parameter keywords
# http://www.remotesensing.org/geotiff/proj_list/

# All crs versions and possible parameters are located in bunch of csv files
# http://svn.osgeo.org/metacrs/geotiff/trunk/libgeotiff/csv/

class VectorCoordRefSys:
    def __init__(self, name, **params):
        pass
