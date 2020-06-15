#
# create scrolled canvas
# straight from http://effbot.org/zone/tkinter-autoscrollbar.htm
# changed to being a class

import sys
if sys.version.startswith("2"):
    import Tkinter as tk
    import tkFont
else:
    import tkinter as tk
    import tkinter.font as tkFont
import ttk
from . import mixins as mx

class _AutoScrollbar(ttk.Scrollbar):
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        ttk.Scrollbar.set(self, lo, hi)
    def pack(self, **kw):
        raise tk.TclError, "cannot use pack with this widget"
    def place(self, **kw):
        raise tk.TclError, "cannot use place with this widget"

class Listbox(tk.Frame, mx.AllMixins):
    def __init__(self, master, items=[], *args, **kwargs):
        master = mx.get_master(master)
        tk.Frame.__init__(self, master)
        mx.AllMixins.__init__(self, master)

        vscrollbar = _AutoScrollbar(self, orient=tk.VERTICAL)
        vscrollbar.grid(row=0, column=1, sticky="ns")
        hscrollbar = _AutoScrollbar(self, orient=tk.HORIZONTAL)
        hscrollbar.grid(row=1, column=0, sticky="ew")
        
        self.listbox = tk.Listbox(self,
                                 yscrollcommand=vscrollbar.set,
                                 xscrollcommand=hscrollbar.set)

        # default list box behavior
        if "activestyle" not in kwargs: kwargs["activestyle"] = "none"
        if "highlightthickness" not in kwargs: kwargs["highlightthickness"] = 0
        if "selectmode" not in kwargs: kwargs["selectmode"] = "extended"
        self.listbox.config(*args, **kwargs)
        
        vscrollbar.config(command=self.listbox.yview)
        hscrollbar.config(command=self.listbox.xview)
        self.listbox.grid(row=0, column=0, sticky="nsew")

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        vscrollbar.grid_rowconfigure(0, weight=1)
        hscrollbar.grid_columnconfigure(0, weight=1)

        for item in items:
            self.listbox.insert("end", str(item))

    # ADD CUSTOM OVERRIDE METHODS THAT REDIRECT TO self.listbox
    # ...

    def insert(self, *args, **kwargs):
        return self.listbox.insert(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.listbox.delete(*args, **kwargs)

    def get(self, *args, **kwargs):
        if args:
            return self.listbox.get(*args, **kwargs)
        else:
            # no specific index requested, so get all items in the list
            return self.listbox.get(0, tk.END)

    def curselection(self, *args, **kwargs):
        return self.listbox.curselection(*args, **kwargs)

##class Listbox(tk.Listbox, mx.AllMixins):
##    def __init__(self, master, items=[], *args, **kwargs):
##
##        tk.Listbox.__init__(self, master)
##        mx.AllMixins.__init__(self, master)
##
##        vscrollbar = _AutoScrollbar(self, orient=tk.VERTICAL)
##        vscrollbar.grid(row=0, column=1, sticky="ns")
##        #vscrollbar.grid_configure(rowspan=2)
##        hscrollbar = _AutoScrollbar(self, orient=tk.HORIZONTAL)
##        hscrollbar.grid(row=1, column=0, sticky="ew")
##
##        # default list box behavior
##        if "activestyle" not in kwargs: kwargs["activestyle"] = "none"
##        if "highlightthickness" not in kwargs: kwargs["highlightthickness"] = 0
##        if "selectmode" not in kwargs: kwargs["selectmode"] = "extended"
##        self.config(yscrollcommand=vscrollbar.set,
##                     xscrollcommand=hscrollbar.set,
##                     *args, **kwargs)
##        print kwargs
##        print self.config
##    
##        vscrollbar.config(command=self.yview)
##        hscrollbar.config(command=self.xview)
##        
####        self.grid_rowconfigure(0, weight=1)
####        self.grid_columnconfigure(0, weight=1)
####        vscrollbar.grid_rowconfigure(0, weight=1)
####        hscrollbar.grid_columnconfigure(0, weight=1)
##
##        for item in items:
##            self.insert("end", str(item))

class Canvas(mx.AllMixins, tk.Canvas):
    def __init__(self, parent, *args, **kwargs):

        # control main frame widget args
        frameargs = kwargs.copy()
        anchor = frameargs.pop("anchor", None)

        # subclass
        parent = mx.get_master(parent)
        tk.Canvas.__init__(self, parent, *args, **frameargs)
        mx.AllMixins.__init__(self, parent)
        
        # begin
        vscrollbar = _AutoScrollbar(self)
        vscrollbar.grid(row=0, column=1, sticky="ns")
        hscrollbar = _AutoScrollbar(self, orient=tk.HORIZONTAL)
        hscrollbar.grid(row=1, column=0, sticky="ew")

        self.config(yscrollcommand=vscrollbar.set,
                    xscrollcommand=hscrollbar.set)
        vscrollbar.config(command=self.yview)
        hscrollbar.config(command=self.xview)

        # make the canvas expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        vscrollbar.grid_rowconfigure(0, weight=1)
        hscrollbar.grid_columnconfigure(0, weight=1)

        size = (self.cget("width"), self.cget("height"))
        self.config(scrollregion="0 0 %s %s" % size)

        # ALSO ALLOW PANNING
        self.bind("<Button-1>",
                  lambda event: self.scan_mark(event.x, event.y),
                  "+")
        self.bind("<Button1-Motion>",
                  lambda event: self.scan_dragto(event.x, event.y, 1),
                  "+")

    def zoom(self, event, level):
        # NOT SURE IF WORKS CORRECTLY
        
        # scale
        value = level * (1 / float(self._zoomlevel))
        self._zoomlevel = level
        # offset
        x1,y1,x2,y2 = self.bbox("all")
        width = max((x1,x2))-min((x1,x2))
        height = max((y1,y2))-min((y1,y2))
        xoff,yoff = min((x1,x2))+width/2.0, min((y1,y2))+height/2.0
        # execute
        self.scale("all",xoff,yoff,value,value)

    def await_draw_point(self):
        def place_button(event):
            self.create_rectangle(event.x, event.y, event.x+10, event.y+10)
            #self.unbind(bindid)
        bindid = self.bind("<Button-3>", place_button, "+")

    def await_draw_lines(self):
        coords = []
        vertexids = []
        lineids = []
        mousevertex = self.create_rectangle(0-5, 0-5, 0+5, 0+5)
        mouseline = self.create_line(0-5, 0-5, 0+5, 0+5, dash=(3,3))

        def add_vertex(event):
            # draw line
            if len(coords) >= 1:
                lineid = self.create_line(coords[-1][0], coords[-1][1], event.x, event.y)
                lineids.append(lineid)
                
            # draw point
            coords.append((event.x, event.y))
            vertexid = self.create_rectangle(event.x-5, event.y-5, event.x+5, event.y+5)
            vertexids.append(vertexid)

        def mouse_moves(event):
            self.coords(mousevertex, event.x-5, event.y-5, event.x+5, event.y+5)
            if len(coords) >= 1:
                self.coords(mouseline, coords[-1][0], coords[-1][1], event.x, event.y)

        avid = self.bind("<Button-1>", add_vertex, "+")
        mmid = self.bind("<Motion>", mouse_moves, "+")

        def undo(event):
            del coords[-1]
            self.delete(vertexids.pop(-1))
            self.delete(lineids.pop(-1))
        
        unid = self.bind_all("<BackSpace>", undo, "+")

        def finish(event):
            self.delete(mousevertex)
            self.delete(mouseline)
            self.unbind("<Button-1>", avid)
            self.unbind("<Motion>", mmid)
            self.unbind("<BackSpace>", undo)
            
        self.bind("<Button-3>", finish, "+")

class Frame(mx.AllMixins, tk.LabelFrame):
    def __init__(self, parent, *args, **kwargs):
        # subclass
        parent = mx.get_master(parent)
        if "label" in kwargs:
            kwargs["text"] = kwargs.pop("label")
        tk.LabelFrame.__init__(self, parent, *args, **kwargs)
        mx.AllMixins.__init__(self, parent)

class ScrollFrame(mx.AllMixins, tk.LabelFrame):
    """
    This "super frame" combines the features of normal frames and labelframes,
    and making it all automatically scrollable.
    
    Use the 'interior' attribute to place widgets inside the scrollable frame.
    All inserted widgets are unified with the kwargs to make it all appear as one widget.

    - anchor: Where to anchor the interior frame. Any of n, s, e, w, or combination of two of them. 
    
    Note: Currently only pack and place are scrollable, grid does not work for some reason (TODO, fix and cleanup internal placement)
    Note: For anchor to work when using pack, must use fill=both, expand=True
    
    """
    def __init__(self, parent, *args, **kwargs):

        # control main frame widget args
        frameargs = kwargs.copy()
        anchor = frameargs.pop("anchor", None)
        if "label" in frameargs:
            frameargs["text"] = frameargs.pop("label")
        if not "relief" in frameargs and not frameargs.get("text",None) and not "labelwidget" in frameargs:
            frameargs["relief"] = "flat"
            frameargs["borderwidth"] = 0

        # control interior frame for inserted widget args
        interiorargs = kwargs.copy()
        interiorargs.pop("anchor", None)
        interiorargs.pop("width", None)
        interiorargs.pop("height", None)

        # also filter out labelframe options for the regular frame interior
        interiorargs.pop("text", None)
        interiorargs.pop("label", None)
        interiorargs.pop("labelanchor", None)
        interiorargs.pop("labelwidget", None)
        
        # subclass
        parent = mx.get_master(parent)
        tk.LabelFrame.__init__(self, parent, *args, **frameargs)
        mx.AllMixins.__init__(self, parent)

        # begin
        vscrollbar = _AutoScrollbar(self)
        vscrollbar.grid(row=0, column=1, sticky="ns")
        hscrollbar = _AutoScrollbar(self, orient=tk.HORIZONTAL)
        hscrollbar.grid(row=1, column=0, sticky="ew")

        self.canvas = tk.Canvas(self,
                        yscrollcommand=vscrollbar.set,
                        xscrollcommand=hscrollbar.set,
                        bg=kwargs.get("bg"),
                        #bd=0, highlightthickness=0,
                        )
        self.canvas.grid(row=0, column=0, sticky="nsew")

        vscrollbar.config(command=self.canvas.yview)
        hscrollbar.config(command=self.canvas.xview)

        # make the canvas expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        vscrollbar.grid_rowconfigure(0, weight=1)
        hscrollbar.grid_columnconfigure(0, weight=1)

        # create canvas contents

        self.interior = ttk.Frame(self.canvas, **interiorargs)
        #self.interior.place(x=0, y=0) #relwidth=1, relheight=1)
        #self.interior.pack(fill="both", expand=True)
        #self.interior.rowconfigure(1, weight=1)
        #self.interior.columnconfigure(1, weight=1)

        interior_id = self.canvas.create_window(0, 0, window=self.interior, anchor="nw")

        # on resize
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (self.interior.winfo_reqwidth(), self.interior.winfo_reqheight())
            self.canvas.config(scrollregion="0 0 %s %s" % size)
            if self.interior.winfo_reqwidth() != self.canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                self.canvas.config(width=self.interior.winfo_reqwidth())
            if self.interior.winfo_reqheight() != self.canvas.winfo_height():
                # update the canvas's height to fit the inner frame
                self.canvas.config(height=self.interior.winfo_reqheight())
        self.interior.bind('<Configure>', _configure_interior)

        # allow mouse scroll
        def _scroll(event):
            try: widget = self.winfo_containing(event.x_root, event.y_root)
            except: widget = None
            while widget:
                if isinstance(widget, ScrollFrame):
                    # scrollframe found
                    if event.delta < 0:
                        widget.canvas.yview_scroll(1, "units")
                    elif event.delta > 0:
                        widget.canvas.yview_scroll(-1, "units")
                    break
                elif hasattr(widget, "master"):
                    # check parent widget, in search of a parent scrollframe
                    widget = widget.master
                else:
                    # reached application root top level, no scrollframe found
                    break
        self.bind_all("<MouseWheel>", _scroll, "+")

    # ADD CUSTOM OVERRIDE METHODS THAT REDIRECT TO self.interior
    # ...

class Treeview(mx.AllMixins, tk.LabelFrame):
    def __init__(self, master, **kwargs):
        master = mx.get_master(master)
        tk.LabelFrame.__init__(self, master) # doesnt yet allow frame label...
        mx.AllMixins.__init__(self, master)

        self.tree = ttk.Treeview(master, **kwargs)
        ysb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        xsb = ttk.Scrollbar(self, orient="horizontal", command=self.tree.xview)
        self.tree['yscroll'] = ysb.set
        self.tree['xscroll'] = xsb.set

        # add tree and scrollbars to frame
        self.tree.grid(in_=self, row=0, column=0, sticky="nsew")
        ysb.grid(in_=self, row=0, column=1, sticky="ns")
        xsb.grid(in_=self, row=1, column=0, sticky="ew")
         
        # set frame resizing priorities (DOESNT WORK)
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
  
    def heading(self, *args, **kwargs):
        return self.tree.heading(*args, **kwargs)

    def column(self, *args, **kwargs):
        return self.tree.column(*args, **kwargs)
    
    def insert(self, *args, **kwargs):
        return self.tree.insert(*args, **kwargs)

    def delete(self, *args, **kwargs):
        return self.tree.delete(*args, **kwargs)


class Table(Treeview):
    def __init__(self, master, **kwargs):
        Treeview.__init__(self, master)
        # restrict icon column
        self.column("#0", stretch=False, width=50)

##    def values(self, field):
##        # TODO: should have better validation, eg by specifying type for each column instead of guessing
##        # or by storing the populated rows, and just mirroring them in the table
##        
##        def value_from_string(val):
##            try:
##                # see if maybe converts to some python type
##                return float(val)
##            except:
##                # check for missing
##                if val == "None":
##                    return None
##                elif val == "nan":
##                    return float("nan")
##                else:
##                    # is supposed to be string
##                    return val
##
##        tree = self.tree
##        for childid in tree.get_children(''):
##            valuestring = tree.set(childid, field)
##            value = value_from_string(valuestring)
##            yield childid, value

    def populate(self, fields, rows):
        # define column indexes/names
        self.tree["columns"] = fields

        self.delete(*self.tree.get_children())

        # column options...
        self.fields = list(fields)
        for f in fields:
            self.heading(f, text=f, command=lambda f=f: self.sortby(f, 0))
            self.column(f, width=tkFont.Font().measure(f))

        # rows
        self.rows = list(rows)
        for i,row in enumerate(self.rows):
            self.insert('', 'end', text=i+1, values=row)

    def sortby(self, field, descending):
        tree = self.tree
        fieldindex = self.fields.index(field)
        ids_rows = zip(tree.get_children(''), self.rows)
        sort = sorted(ids_rows, key=lambda(_id,row): row[fieldindex], reverse=descending)
        for indx, (_id,row) in enumerate(sort):
            tree.move(_id, '', indx)
        self.rows = [row for _id,row in sort]

        tree.heading(field,
                    command=lambda field=field: self.sortby(field, int(not descending)))

class OrderedList(mx.AllMixins, tk.LabelFrame):
    def __init__(self, master, **kwargs):
        """
        Should have predefined bindings for drag and drop, as a shallow wrapper around
        a real list, all changes affecting the order of the underlying model. 
        """
        master = mx.get_master(master)
        tk.LabelFrame.__init__(self, master) # doesnt yet allow frame label...
        mx.AllMixins.__init__(self, master)

        # Make the top header
        self.header = tk.Label(self, text=kwargs.get('title', "Items:"))
        self.header.pack(side="top", anchor=kwargs.get('titleanchor', 'w'))

        self.items = []
        self.listarea = ScrollFrame(self)
        self.listarea.pack(fill="both", expand=1)

    def add_item(self, item, decorate=None):
        widget = OrderedListItem(self.listarea.interior, item)
        widget.pack()
        if not decorate:
            def decorate(w):
                w["text"] = repr(w.item)[:50]
        decorate(widget)
        self.items.append(widget)
        return widget

class OrderedListItem(mx.AllMixins, tk.Frame):
    def __init__(self, master, item, **kwargs):
        master = mx.get_master(master)
        tk.Frame.__init__(self, master) # doesnt yet allow frame label...
        mx.AllMixins.__init__(self, master)

        self.item = item
