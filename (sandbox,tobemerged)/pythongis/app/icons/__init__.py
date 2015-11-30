
import os
import pyagg

ICONSFOLDER = os.path.split(__file__)[0]


def get(iconname):
    iconpath = os.path.join(ICONSFOLDER, iconname)
    if os.path.lexists(iconpath):
        return pyagg.load(iconpath)
    else: raise Exception("No icon by that name")
