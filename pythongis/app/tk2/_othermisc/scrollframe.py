#
# create scrolled canvas
# straight from http://effbot.org/zone/tkinter-autoscrollbar.htm
# changed to being a class

from Tkinter import *
#from ttk import *
import random

class AutoScrollbar(Scrollbar):
    # a scrollbar that hides itself if it's not needed.  only
    # works if you use the grid geometry manager.
    def set(self, lo, hi):
        if float(lo) <= 0.0 and float(hi) >= 1.0:
            # grid_remove is currently missing from Tkinter!
            self.tk.call("grid", "remove", self)
        else:
            self.grid()
        Scrollbar.set(self, lo, hi)
    def pack(self, **kw):
        raise TclError, "cannot use pack with this widget"
    def place(self, **kw):
        raise TclError, "cannot use place with this widget"

class ScrollableCanvas(Canvas):
    def __init__(self, parent, *args, **kwargs):

        # control main frame widget args
        frameargs = kwargs.copy()
        anchor = frameargs.pop("anchor", None)
        if not frameargs.get("bg"):
            frameargs["bg"] = self.color("random")

        # subclass
        Canvas.__init__(self, parent, *args, **frameargs)
        
        # begin
        vscrollbar = AutoScrollbar(self)
        vscrollbar.grid(row=0, column=1, sticky=N+S)
        hscrollbar = AutoScrollbar(self, orient=HORIZONTAL)
        hscrollbar.grid(row=1, column=0, sticky=E+W)

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

        # TESTING
        # zoom widget
        def call_on_zoom(event):
            self.zoom(None, scale.get())
        scale = Scale(self, from_=5000, to=1, #resolution=-1,
                      command=call_on_zoom)
        scale.grid(row=0,column=0, sticky="w")
        scale.set(100)
        self._zoomlevel = scale.get()

        # draw more
        drawbut = Button(self, text="draw", command=self.test_draw)
        drawbut.grid(row=0,column=0, sticky="n")
        drawbut.grid_configure(columnspan=2)

        # startup
        self.test_draw()

    def zoom(self, event, level):
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

    def test_draw(self):
        for i in range(4):
            self.create_line([map(random.randrange,[int(self["width"]),int(self["height"])]) for _ in range(7)],
                               width=12,
                               capstyle=ROUND,
                               arrow="last",
                               smooth=True,
                               fill=self.color("random"))

    def color(self, color):
        if color == "random":
            rgb = map(random.randrange,[255,255,255])
        return '#%02x%02x%02x' % tuple(rgb)



class ScrollableFrame(Frame):
    """
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

        # control interior frame for inserted widget args
        interiorargs = kwargs.copy()
        interiorargs.pop("anchor", None)
        interiorargs.pop("width", None)
        interiorargs.pop("height", None)

        # subclass
        Frame.__init__(self, parent, *args, **frameargs)

        # begin
        vscrollbar = AutoScrollbar(self)
        vscrollbar.grid(row=0, column=1, sticky=N+S)
        hscrollbar = AutoScrollbar(self, orient=HORIZONTAL)
        hscrollbar.grid(row=1, column=0, sticky=E+W)

        canvas = Canvas(self,
                        yscrollcommand=vscrollbar.set,
                        xscrollcommand=hscrollbar.set,
                        bg=kwargs.get("bg"),
                        #bd=0, highlightthickness=0,
                        )
        canvas.grid(row=0, column=0, sticky=anchor)

        vscrollbar.config(command=canvas.yview)
        hscrollbar.config(command=canvas.xview)

        # make the canvas expandable
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        vscrollbar.grid_rowconfigure(0, weight=1)
        hscrollbar.grid_columnconfigure(0, weight=1)

        # create canvas contents

        self.interior = Frame(canvas, **interiorargs)
        #self.interior.rowconfigure(1, weight=1)
        #self.interior.columnconfigure(1, weight=1)

        interior_id = canvas.create_window(0, 0, window=self.interior, anchor="nw")

        # on resize
        def _configure_interior(event):
            # update the scrollbars to match the size of the inner frame
            size = (self.interior.winfo_reqwidth(), self.interior.winfo_reqheight())
            canvas.config(scrollregion="0 0 %s %s" % size)
            if self.interior.winfo_reqwidth() != canvas.winfo_width():
                # update the canvas's width to fit the inner frame
                canvas.config(width=self.interior.winfo_reqwidth())
            if self.interior.winfo_reqheight() != canvas.winfo_height():
                # update the canvas's height to fit the inner frame
                canvas.config(height=self.interior.winfo_reqheight())
        self.interior.bind('<Configure>', _configure_interior)

# test it

win = Tk()

canvas = ScrollableCanvas(win, width=1900, height=1900)
canvas.pack(fill="both", expand=True)

top = ScrollableFrame(win, bg="blue", width=700, height=300)
top.pack() #pack(fill="both", expand=True) #place(relx=0,rely=0,relwidth=1,relheight=0.5) #grid(row=0, column=0, sticky="nsew")
for green in range(0, 250, 25):
    bg_hex = '#%02x%02x%02x' % (0,green,0)
    mini = Frame(top.interior, bg=bg_hex, width=100, height=100)
    mini.pack(side="right")
    
bottom = ScrollableFrame(win, bg="orange")
bottom.pack() #pack(fill="both", expand=True) #place(relx=0,rely=0.5,relwidth=1,relheight=0.5) #grid(row=1, column=0, sticky="nsew")
for i in range(1,10):
    for j in range(1,10):
        button = Button(bottom.interior, text="[%d,%d]" % (i,j))
        button.grid(row=i, column=j, sticky='nsew')
i += 1
for j in range(1,7):
    button = Button(bottom.interior, text="[%d,%d]" % (i,j))
    button.grid(row=i, column=j, sticky='nsew')

Button(win, text="hello world").pack() #pack(fill="both", expand=True)
        
win.mainloop()


# original from effbot
##root = Tk()
##
##vscrollbar = AutoScrollbar(root)
##vscrollbar.grid(row=0, column=1, sticky=N+S)
##hscrollbar = AutoScrollbar(root, orient=HORIZONTAL)
##hscrollbar.grid(row=1, column=0, sticky=E+W)
##
##canvas = Canvas(root,
##                yscrollcommand=vscrollbar.set,
##                xscrollcommand=hscrollbar.set)
##canvas.grid(row=0, column=0, sticky=N+S+E+W)
##
##vscrollbar.config(command=canvas.yview)
##hscrollbar.config(command=canvas.xview)
##
### make the canvas expandable
##root.grid_rowconfigure(0, weight=1)
##root.grid_columnconfigure(0, weight=1)
##
###
### create canvas contents
##
##frame = Frame(canvas)
##frame.rowconfigure(1, weight=1)
##frame.columnconfigure(1, weight=1)
##
##rows = 5
##for i in range(1,rows):
##    for j in range(1,10):
##        button = Button(frame, padx=7, pady=7, text="[%d,%d]" % (i,j))
##        button.grid(row=i, column=j, sticky='news')
##
##canvas.create_window(0, 0, anchor=NW, window=frame)
##
##frame.update_idletasks()
##
##canvas.config(scrollregion=canvas.bbox("all"))
##
##root.mainloop()



##
##from Tkinter import *   # from x import * is bad practice
##from ttk import *
##
### http://tkinter.unpythonic.net/wiki/VerticalScrolledFrame
### modified to handle scrollbars in both directions
### Karim Bahgat 2015
##
##class ScrolledFrame(Frame):
##    """A pure Tkinter scrollable frame that actually works!
##    * Use the 'interior' attribute to place widgets inside the scrollable frame
##    * Construct and pack/place/grid normally
##    * The frame allows both vertical and horizontal scrolling
##
##    """
##    def __init__(self, parent, *args, **kw):
##        Frame.__init__(self, parent, *args, **kw) 
##
##        # create a canvas object and a vertical scrollbar for scrolling it
##        vscrollbar = Scrollbar(self, orient=VERTICAL)
##        vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
##        hscrollbar = Scrollbar(self, orient=HORIZONTAL)
##        hscrollbar.pack(fill=X, side=BOTTOM, expand=FALSE)
##        canvas = Canvas(self, bd=0, highlightthickness=0,
##                        yscrollcommand=vscrollbar.set,
##                        xscrollcommand=hscrollbar.set)
##        canvas.pack(side=LEFT, fill=BOTH, expand=TRUE)
##        vscrollbar.config(command=canvas.yview)
##        hscrollbar.config(command=canvas.xview)
##
##        # reset the view
##        canvas.xview_moveto(0)
##        canvas.yview_moveto(0)
##
##        # create a frame inside the canvas which will be scrolled with it
##        self.interior = interior = Frame(canvas)
##        interior_id = canvas.create_window(0, 0, window=interior,
##                                           anchor=NW)
##
##        # track changes to the canvas and frame width and sync them,
##        # also updating the scrollbar
##        def _configure_interior(event):
##            # update the scrollbars to match the size of the inner frame
##            size = (interior.winfo_reqwidth(), interior.winfo_reqheight())
##            canvas.config(scrollregion="0 0 %s %s" % size)
##            if interior.winfo_reqwidth() != canvas.winfo_width():
##                # update the canvas's width to fit the inner frame
##                canvas.config(width=interior.winfo_reqwidth())
##                left,right = hscrollbar.get()
##                print left,right
##                if left == 0 and right == 1:
##                    print "forget"
##                    hscrollbar.pack_forget()
##                else:
##                    print "pack"
##                    hscrollbar.pack(fill=Y, side=BOTTOM, expand=FALSE)
##            if interior.winfo_reqheight() != canvas.winfo_height():
##                # update the canvas's height to fit the inner frame
##                canvas.config(height=interior.winfo_reqheight())
##                # hide the scrollbar if fully expanded
##                top,bottom = vscrollbar.get()
##                print top,bottom
##                if top == 0 and bottom == 1:
##                    print "forget"
##                    vscrollbar.pack_forget()
##                else:
##                    print "pack"
##                    vscrollbar.pack(fill=Y, side=RIGHT, expand=FALSE)
##        canvas.bind('<Configure>', _configure_interior)
##
##        def _configure_canvas(event):
##            if interior.winfo_reqwidth() != canvas.winfo_width():
##                # update the inner frame's width to fill the canvas
##                canvas.itemconfigure(interior_id, width=canvas.winfo_width())
##        canvas.bind('<Configure>', _configure_canvas, "+")
##
##
##if __name__ == "__main__":
##
##    class SampleApp(Tk):
##        def __init__(self, *args, **kwargs):
##            root = Tk.__init__(self, *args, **kwargs)
##
##
##            self.frame = ScrolledFrame(root)
##            self.frame.pack(fill="both", expand=True)
##            self.label = Label(text="Shrink the window to activate the scrollbar.")
##            self.label.pack()
##            buttons = []
##            for i in range(10):
##                buttons.append(Button(self.frame.interior, width=40, text="Button " + str(i)))
##                buttons[-1].pack()
##
##    app = SampleApp()
##    app.mainloop()
