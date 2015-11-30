# build the exe by simply running this script
#import sys
#sys.argv.append("py2exe")

# standard setup file
from distutils.core import setup
import py2exe

# get all dependencies from dependencies folder
# and make sure all dlls and pyds are included
import sys
sys.path.append("pythongis/dependencies")
import os
def allfilesinfolder(rootfolder):
    return [(folder,
             [os.path.join(folder,filename) for filename in files] )
             for folder,_,files in os.walk(rootfolder) ]
DATA = list()
DATA += allfilesinfolder("pythongis")
for dependency in os.listdir("dependencies"):
    DATA += allfilesinfolder("dependencies/%s"%dependency)

options = dict(skip_archive=True,
               #bundle_files=1,
               #compressed=True,
               #excludes=["shapely","rtree","pyagg","PIL","pythongis"],
               #packages=["ctypes","json","xml"],
               dll_excludes=["python26.dll","python27.so","geos_c.dll"],
               packages=["ctypes","shapely","rtree","pyagg","PIL"],
##               excludes=["doctest",
##                        "pdb",
##                        "unittest",
##                        "difflib"]
               )
               
setup(windows=["guitester.py"],
      options={"py2exe": options},
      #zipfile=None,
      data_files=DATA
      )

