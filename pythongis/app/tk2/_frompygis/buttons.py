# Import builtins
import sys, os

# Import GUI libraries
import Tkinter as tk
from tkFileDialog import askopenfilenames, asksaveasfilename
import PIL, PIL.Image, PIL.ImageTk

# Import theme
from . import theme
style_button_normal = {"fg": theme.font1["color"],
                  "font": theme.font1["type"],
                  "bg": theme.color4,
                   "relief": "flat",
                   "activebackground": theme.strongcolor2
                   }
style_button_mouseover = {"bg": theme.strongcolor1
                    }



# Icons folder
TOOLKIT_FOLDER = os.path.split(__file__)[0]
APP_FOLDER = os.path.split(TOOLKIT_FOLDER)[0]
ICONS_FOLDER = os.path.join(APP_FOLDER, "icons")





# Button style and behavior

class Button(tk.Button):
    def __init__(self, master, **kwargs):
        # get theme style
        style = style_button_normal.copy()
        style.update(kwargs)
        
        # initialize
        tk.Button.__init__(self, master, **style)

        # bind event behavior
        def mouse_in(event):
            event.widget.config(style_button_mouseover)
        def mouse_out(event):
            event.widget.config(style_button_normal)

        self.bind("<Enter>", mouse_in)
        self.bind("<Leave>", mouse_out)
        

# Some specialized buttons

class OkButton(Button):
    def __init__(self, master, **kwargs):
        # initialize
        if kwargs.get("text") == None:
            kwargs["text"] = "OK"
        okfunc = kwargs.get("command")
        Button.__init__(self, master, **kwargs)

        # bind enter keypress to command function
        def runfunc(event):
            okfunc()
        self.winfo_toplevel().bind("<Return>", runfunc)

class CancelButton(Button):
    def __init__(self, master, **kwargs):
        # initialize
        if kwargs.get("text") == None:
            kwargs["text"] = "Cancel"
        cancelfunc = kwargs.get("command")
        Button.__init__(self, master, **kwargs)

        # bind enter keypress to command function
        def runfunc(event):
            cancelfunc()
        self.winfo_toplevel().bind("<Escape>", runfunc)
        
class IconButton(Button):
    def __init__(self, master, **kwargs):
        # initialize
        Button.__init__(self, master, **kwargs)

    def set_icon(self, iconname, **kwargs):
        img_path = os.path.join(ICONS_FOLDER, iconname)
        img = PIL.Image.open(img_path)
        # resize if necessary
        width,height = img.size
        if kwargs.get("width"): width = kwargs["width"]
        if kwargs.get("height"): height = kwargs["height"]
        img = img.resize((width, height), PIL.Image.ANTIALIAS)
        # resize button to have room for text if compound type
        if kwargs.get("compound"):
            def expand():
                self["width"] += width
                self["height"] += height/2
            self.after(100, expand)
        # convert to tkinter
        tk_img = PIL.ImageTk.PhotoImage(img)
        if not kwargs.get("anchor"): kwargs["anchor"] = "center"
        self.config(image=tk_img, **kwargs)
        self.img = tk_img

class OpenFileButton(IconButton):
    def __init__(self, master, **kwargs):
        IconButton.__init__(self, master, **kwargs)
        
       
