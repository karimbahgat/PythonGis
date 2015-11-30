############
# allow building the exe by simply running this script
import sys
sys.argv.append("py2exe")

############
### imports
from distutils.core import setup
import py2exe

###########
### options
WINDOWS = [{"script": "guitester.py",
            "icon_resources": [(1,"pythongis/app/logo.ico")] }]
OPTIONS = {"skip_archive": True,
           "dll_excludes": ["python26.dll","python27.so"],
           "excludes": ["numpy"],
           }

###########
### create the application icon
##import PIL, PIL.Image
##img = PIL.Image.open("icon.png")
##img.save("icon.ico", sizes=[(255,255),(128,128),(64,64),(48,48),(32,32),(16,16),(8,8)])

###########
### build
setup(windows=WINDOWS,
      options={"py2exe": OPTIONS}
      )

###########
### manually copy pythongis package to dist
### ...because py2exe may not copy all files
import os
import shutil
frompath = "pythongis"
topath = os.path.join("dist","pythongis")
shutil.rmtree(topath) # deletes the folder copied by py2exe
shutil.copytree(frompath, topath)

###########
### and same with advanced dependencies
### ...only packages, ie folders
site_packages_folder = "C:/Python27/Lib/site-packages"
advanced_dependencies = ["PIL", "pyagg", "rtree", "shapely"]
for dependname in advanced_dependencies:
    frompath = os.path.join(site_packages_folder, dependname)
    topath = os.path.join("dist", dependname)
    print frompath,topath
    shutil.rmtree(topath) # deletes the folder copied by py2exe
    shutil.copytree(frompath, topath)
