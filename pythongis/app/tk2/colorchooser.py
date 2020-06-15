
import sys
if sys.version.startswith("2"):
    from tkColorChooser import askcolor
else:
    from tkinter.colorchoser import askcolor
