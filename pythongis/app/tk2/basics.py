"""
Tk2
Tk2 is a convenience library for extending the functionality of Tkinter, 
to make it easier and more flexible to create GUI applications. 
"""


# Imports

import sys
if sys.version.startswith("2"):
    import Tkinter as tk
else: import tkinter as tk
import ttk
from . import mixins as mx
from . import scrollwidgets
from . import variables as vr
from . import colorchooser


# Classes

class Label(mx.AllMixins, ttk.Label):
    def __init__(self, master, **kwargs):
        master = mx.get_master(master)
        ttk.Label.__init__(self, master, **kwargs)
        mx.AllMixins.__init__(self, master)
        
        ## self.bind_rightclick( [("Edit", self.edit_text)] )

##    def edit_text(self):
##        # doesnt work, maybe remove...
##        entry = Entry(self)
##        entry.insert(0, self["text"])
##        entry.pack()
##        def dropentry(event):
##            entry.destroy()
##        def acceptentry(event):
##            self["text"] = entry.get()
##            entry.destroy()
##        entry.bind_once("<Escape>", dropentry)
##        entry.bind_once("<Return>", acceptentry)

class Entry(Label):
    def __init__(self, master, **kwargs):
        master = mx.get_master(master)
        Label.__init__(self, master)

        # add label
        if "label" in kwargs:
            label = tk.Label(self, text=kwargs.pop("label"))
            label.pack(side=kwargs.pop("labelside","left"))

##        placeholder = kwargs.pop("placeholder",None)
        defaultval = kwargs.pop("default",None)
        if not "textvariable" in kwargs:
            kwargs["textvariable"] = vr.StringVar()
        self.var = kwargs["textvariable"]

        entry = self.entry = ttk.Entry(self, **kwargs)
        entry.pack(side=kwargs.pop("entryside","right"))

        # placeholder
        # (not finished yet...)
##        if placeholder:
##            def focusin(*pointless):
##                if entry._placedummy:
##                    kwargs["textvariable"].set("")
##            def focusout(*pointless):
##                if not entry._placedummy and not kwargs["textvariable"].get():
##                    entry["foreground"] = "grey"
##                    kwargs["textvariable"].set(placeholder)
##                    entry._placedummy = True
##                else:
##                    entry["foreground"] = "black"
##                    entry._placedummy = False
##            #kwargs["textvariable"].trace("w", checkempty)
##            entry.bind("<FocusIn>", focusin)
##            entry.bind("<FocusOut>", focusout)

        # default value
        if defaultval:
            self.var.set(defaultval)
            
##        else:
##            entry._placedummy = True
##            kwargs["textvariable"].set(placeholder)
##            entry["foreground"] = "grey"

        self.interior = entry

##    def __getattr__(self, attr):
##        return self.__getattribute__(attr)

    def set(self, value):
        return self.var.set(value)

    def get(self):
        return self.var.get()

    def insert(self, *args, **kwargs):
        self.interior.insert(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.interior.delete(*args, **kwargs)

    def focus(self):
        self.entry.focus()

class Checkbutton(mx.AllMixins, tk.Checkbutton):
    def __init__(self, master, **kwargs):
        master = mx.get_master(master)
        tk.Checkbutton.__init__(self, master, **kwargs)
        mx.AllMixins.__init__(self, master)

        if not "variable" in kwargs:
            kwargs["variable"] = vr.IntVar()
        self.var = kwargs["variable"]

    def get(self):
        return self.var.get()

class Radiobutton(mx.AllMixins, tk.Radiobutton):
    def __init__(self, master, **kwargs):
        master = mx.get_master(master)
        tk.Radiobutton.__init__(self, master, **kwargs)
        mx.AllMixins.__init__(self, master)

class Dropdown(mx.AllMixins, tk.Label):
    def __init__(self, master, **kwargs):
        master = mx.get_master(master)
        tk.Label.__init__(self, master)
        mx.AllMixins.__init__(self, master)

        # add label
        if "label" in kwargs:
            label = tk.Label(self, text=kwargs.pop("label"))
            label.pack(side=kwargs.pop("labelside","left"))

        combobox = ttk.Combobox(self, **kwargs)
        combobox.pack(side=kwargs.pop("entryside","right"))
        self.interior = combobox

    def set(self, value):
        return self.interior.set(value)

    def get(self):
        return self.interior.get()

    def __getitem__(self, item):
        return self.interior[item]
        
    def __setitem__(self, item, val):
        self.interior[item] = val

class Separator(mx.AllMixins, ttk.Separator):
    def __init__(self, master, **kwargs):
        master = mx.get_master(master)
        ttk.Separator.__init__(self, master, **kwargs)
        mx.AllMixins.__init__(self, master)

class Sizegrip(mx.AllMixins, ttk.Sizegrip):
    def __init__(self, master, **kwargs):
        master = mx.get_master(master)
        ttk.Sizegrip.__init__(self, master, **kwargs)
        mx.AllMixins.__init__(self, master)

class Scrollbar(mx.AllMixins, ttk.Scrollbar):
    def __init__(self, master, **kwargs):
        master = mx.get_master(master)
        ttk.Scrollbar.__init__(self, master, **kwargs)
        mx.AllMixins.__init__(self, master)

class Menubutton(mx.AllMixins, ttk.Menubutton):
    # not sure what does/how differs from normal Menu()...
    def __init__(self, master, **kwargs):
        master = mx.get_master(master)
        ttk.Menubutton.__init__(self, master, **kwargs)
        mx.AllMixins.__init__(self, master)

class Slider(mx.AllMixins, ttk.Scale):
    def __init__(self, master, *args, **kwargs):
        master = mx.get_master(master)
        ttk.Scale.__init__(self, master, *args, **kwargs)
        mx.AllMixins.__init__(self, master)

##class Listbox(tk.Frame, mx.AllMixins):
##    def __init__(self, master, items=[], *args, **kwargs):
##        master = mx.get_master(master)
##        tk.Frame.__init__(self, master, *args, **kwargs)
##        mx.AllMixins.__init__(self, master)
##
##        scrollbar = Scrollbar(self, orient="vertical")
##        listbox = tk.Listbox(self, yscrollcommand=scrollbar.set,
##                          activestyle="none",
##                          highlightthickness=0, selectmode="extended")
##        scrollbar.config(command=listbox.yview)
##        scrollbar.pack(side="right", fill="y")
##        listbox.pack(side="left", fill="both", expand=True)
##
##        for item in items:
##            listbox.insert("end", str(item))
        






# Unify Tk(), Window

class Tk(mx.AllMixins, tk.Tk):
    def __init__(self):
        tk.Tk.__init__(self)
        mx.AllMixins.__init__(self)
        # Force and lock focus to the window
        self.grab_set()
        self.focus_force()

    def center(self):
        # Set its size to percent of screen size, and place in middle
        def _center(*bl):
            if self.winfo_viewable():
                width = self.winfo_reqwidth()
                height = self.winfo_reqheight()
                xleft = self.winfo_screenwidth()/2.0 - width / 2.0
                ytop = self.winfo_screenheight()/2.0 - height / 2.0
                self.geometry("+%i+%i"%(xleft, ytop))
            else:
                # wait for window to have been populated/viewable
                # to get the correct reqwidth/reqheight
                self.after(10,_center)

        self.after(10, _center)
        
        
class Window(mx.AllMixins, tk.Toplevel):
    def __init__(self, master=None, **kwargs):
        # Make this class a subclass of tk.Menu and add to it
        master = mx.get_master(master)
        tk.Toplevel.__init__(self, master, **kwargs)
        mx.AllMixins.__init__(self, master)
        # Force and lock focus to the window
        self.grab_set()
        self.focus_force()
        
    def center(self):
        # Set its size to percent of screen size, and place in middle
        def _center(*bl):
            if self.winfo_viewable():
                width = self.winfo_reqwidth()
                height = self.winfo_reqheight()
                xleft = self.winfo_screenwidth()/2.0 - width / 2.0
                ytop = self.winfo_screenheight()/2.0 - height / 2.0
                self.geometry("+%i+%i"%(xleft, ytop))
            else:
                # wait for window to have been populated/viewable
                # to get the correct reqwidth/reqheight
                self.after(10,_center)

        self.after(10, _center)



# Complete the button widgets!

class Button(mx.AllMixins, ttk.Button):
    def __init__(self, master, **kwargs):
        # initialize
        master = mx.get_master(master)
        ttk.Button.__init__(self, master, **kwargs)
        mx.AllMixins.__init__(self, master)

    def set_icon(self, filepath, **kwargs):
        """
        image given as filepath
        """
        import PIL, PIL.Image, PIL.ImageTk
        img = PIL.Image.open(filepath)
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
        #if not kwargs.get("anchor"): kwargs["anchor"] = "center"
        self.config(image=tk_img) #, **kwargs)
        self.img = tk_img

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

        # bind escape keypress to command function
        def runfunc(event):
            cancelfunc()
        self.winfo_toplevel().bind("<Escape>", runfunc)

class ColorButton(Button):
    def __init__(self, master, **kwargs):
        # initialize
        Button.__init__(self, master, **kwargs)
        self._img = None

        # maybe set random starting color?
        choosefunc = kwargs.get("command")
        def wrapfunc():
            rgb,hexdec = colorchooser.askcolor()
            self.set_color(rgb)
            if choosefunc:
                choosefunc()
        self['command'] = wrapfunc

    def set_color(self, rgb, width=None, height=None):
        #fill button image with the given color in a tkphotoimage
        if not width:
            if self._img: width = self._img.width()
            else: width = self.winfo_reqwidth()
        if not height:
            if self._img: height = self._img.height()
            else: height = self.winfo_reqheight()
        img = tk.PhotoImage(width=width, height=height)
        imgstring = " ".join(["{"+" ".join(["#%02x%02x%02x" %tuple(rgb) for _ in range(width)])+"}" for _ in range(height)])
        img.put(imgstring)
        self._img = img
        self["image"] = img


# Add PanedWindow

class Panes(mx.AllMixins, tk.PanedWindow):
    def __init__(self, master, panes=1, **kwargs):
        # initialize
        if "sashrelief" not in kwargs:
            kwargs["sashrelief"] = "ridge"
        master = mx.get_master(master)
        tk.PanedWindow.__init__(self, master, **kwargs)
        mx.AllMixins.__init__(self, master)

        # add all panes at startup
        #for _ in range(panes):
        #    fr = tk.Frame(self)
        #    self.add(fr)

    def add_pane(self):
        # panedwindow only takes pure tkinter widgets
        # so first create a normal frame to be added
        fr = tk.Frame(self)
        fr.pack(fill="both", expand=True)
        self.add(fr)
        # then nest a tk2 frame inside it and return it
        # ...
        return fr

    def get_pane(self, nameorindex):
        # get pane by name or index
        pass



# Toolbar (simply a draggable frame)

class Toolbar(mx.AllMixins, ttk.LabelFrame):
    # not sure what does/how differs from normal Menu()...
    def __init__(self, master, **kwargs):
        master = mx.get_master(master)
        ttk.LabelFrame.__init__(self, master, **kwargs)
        mx.AllMixins.__init__(self, master)

        # make draggable
        self.bind_draggable()




##class Toolbar(tk.Frame):
##    """
##    Base class for all toolbars.
##    """
##    def __init__(self, master, toolbarname, **kwargs):
##        # get theme style
##        style = style_toolbar_normal.copy()
##        style.update(kwargs)
##        
##        # Make this class a subclass of tk.Frame and add to it
##        tk.Frame.__init__(self, master, **style)
##
##        # Divide into button area and toolbar name
##        self.buttonframe = tk.Frame(self, **style)
##        self.buttonframe.pack(side="top", fill="y", expand=True)
##        self.name_label = tk.Label(self, **style_namelabel_normal)
##        self.name_label["text"] = toolbarname
##        self.name_label.pack(side="bottom")
##
##    def add_button(self, icon=None, **kwargs):
##        button = IconButton(self.buttonframe)
##        options = {"text":"", "width":48, "height":32, "compound":"top"}
##        options.update(kwargs)
##        if icon:
##            button.set_icon(icon, **options)
##        else:
##            button.config(**options)
##        button.pack(side="left", padx=2, pady=0, anchor="center")
##        return button




###########
# LATER:
###########

# Tooltip (info box that follows mouse when hovering)

# Orderedlist

# Calendar, Clock, and Table...

# Add all other messageboxes in py3 structure
### http://stackoverflow.com/questions/673174/file-dialogs-of-tkinter-in-python-3/673309#673309


        
