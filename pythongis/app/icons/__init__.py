
import PIL, PIL.Image, PIL.ImageTk
import os

def iconpath(name):
    return os.path.join(os.path.dirname(__file__), name)

def get(iconname, width=30, height=30):
    im = PIL.Image.open(iconpath(iconname))
    im = im.resize((width,height))
    tkim = PIL.ImageTk.PhotoImage(image=im)
    return tkim
