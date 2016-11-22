# Import builtins
import sys, os

# Import GUI libraries
import Tkinter as tk
from tkFileDialog import askopenfilenames, asksaveasfilename
import PIL, PIL.Image, PIL.ImageTk

# Import internals
from .. import icons

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
        # get icon as tkinter photoimage, with an optional resize
        tk_img = icons.get(iconname,
                           width=kwargs.get("width"),
                           height=kwargs.get("height"))
        self.config(image=tk_img, **kwargs)
        # resize button to have room for text if compound type
        if not kwargs.get("anchor"): kwargs["anchor"] = "center"
        if kwargs.get("compound"):
            def expand():
                self["width"] += tk_img.width()
                self["height"] += tk_img.height() / 2
            self.after(100, expand)
        # store as attribute, so it doesn't get garbage collected
        self.tk_img = tk_img


        
       
