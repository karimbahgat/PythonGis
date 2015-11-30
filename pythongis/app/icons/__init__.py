
import os
import PIL.Image, PIL.ImageTk

ICONSFOLDER = os.path.split(__file__)[0]

def get(iconname, width=None, height=None):
    iconpath = os.path.join(ICONSFOLDER, iconname)
    
    if os.path.lexists(iconpath):
        img = PIL.Image.open(iconpath)
        if width or height:
            width = width or img.size[0]
            height = height or img.size[1]
            img = img.resize((width,height), PIL.Image.ANTIALIAS)
        tk_img = PIL.ImageTk.PhotoImage(img)
        return tk_img
    
    else:
        raise Exception("No icon by that name")
