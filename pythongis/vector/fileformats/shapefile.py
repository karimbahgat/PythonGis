"""
TODO: Switch to a fileformat class that iterates the source data, instead of loading
all into memory... 
"""

# import builtins
import os
import csv
import codecs
import itertools
import warnings

# import fileformat modules
import shapefile as pyshp





class Shapefile(object):
    def __init__(self, filepath, encoding="utf8", encoding_errors="strict", **kwargs):

        if filepath:
            # reading from file
            self.filepath = filepath
            if not filepath.endswith('.shp'):
                raise Exception("This is not a valid shapefile extension format.")

            self.select = kwargs.pop("select")
            self.shapereader = pyshp.Reader(filepath, **kwargs) # TODO: does pyshp take kwargs?
            
            # load fields
            self.fields = [decode(fieldinfo[0]) for fieldinfo in self.shapereader.fields[1:]]
            
            # load projection string from .prj file if exists
            if os.path.lexists(filepath[:-4] + ".prj"):
                self.crs = open(filepath[:-4] + ".prj", "r").read()
            else: self.crs = "+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs"

        else:
            # only writing to file
            self.fields = []

    def __iter__(self):
        # iterate existing file
        for feat in self.shapereader.iterShapeRecords():
            rowdict = dict(zip(self.fields,feat.record))
            if self.select(rowdict):
                geoj = feat.shape.__geo_interface__
                if hasattr(obj, "bbox"): geoj["bbox"] = list(obj.bbox)
                yield rowdict, geoj

    def __len__(self):
        dasa

    def __getitem__(self, i):
        fdsfsd






