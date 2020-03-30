
from .map import MapView
from . import icons

import pythongis as pg
import tk2

class TableGUI(tk2.Tk):
    def __init__(self, *args, **kwargs):
        tk2.basics.Tk.__init__(self, *args, **kwargs)

        self.browser = TableBrowser(self)
        self.browser.pack(fill="both", expand=1)

        self.state('zoomed')

class SimpleMapViewerGUI(tk2.Tk):
    # new experimental version
    def __init__(self, mapp, time=False, *args, **kwargs):
        tk2.basics.Tk.__init__(self, *args, **kwargs)

        ###
        
        mainframe = tk2.Frame(self)
        mainframe.pack(side='left', fill='both', expand=1)

        layersframe = tk2.Frame(self)
        layersframe.pack(side='right', fill='y', expand=0)

        ###

        mapframe = tk2.Frame(mainframe) #bd=10, relief='flat') #, background='black')
        mapframe.pack(fill='both', expand=1)

        mapview = self.mapview = pg.app.map.MapView(mapframe, mapp)
        mapview.pack(fill="both", expand=1)

        bottombar = self.bottombar = tk2.Label(mainframe) #, background='red')
        bottombar.pack(fill='x', expand=0)

        layerscontrol = pg.app.controls.StaticLayersControl(layersframe)
        layerscontrol.pack(fill='y', expand=1) #place(relx=0.99, rely=0.02, anchor="ne")
        mapview.add_control(layerscontrol)
        layerscontrol.set_layers(mapp.layers)

        navigcontrol = pg.app.controls.NavigateControl(bottombar)
        navigcontrol.pack(side='left')
        mapview.add_control(navigcontrol)

        def ask_save():
            filepath = tk2.filedialog.asksaveasfilename()
            mapview.renderer.img.save(filepath)
        savebut = tk2.Button(bottombar, command=ask_save)
        savebut.set_icon(icons.iconpath("save.png"), width=40, height=40)
        savebut.pack(side="right") #pack(fill='y', expand=1, side="right") #place(relx=0.02, rely=0.02, anchor="nw")

        identcontrol = pg.app.controls.IdentifyControl(bottombar)
        identcontrol.pack(side="right") #place(relx=0.98, rely=0.11, anchor="ne")
        mapview.add_control(identcontrol)

        measurecontrol = pg.app.controls.MeasureControl(bottombar)
        measurecontrol.pack(side="right") #place(relx=0.98, rely=0.11, anchor="ne")
        mapview.add_control(measurecontrol)

        projcontrol = pg.app.controls.MapProjectionControl(bottombar)
        projcontrol.pack(side="right") #place(relx=0.98, rely=0.11, anchor="ne")
        mapview.add_control(projcontrol)

        zoomhistcontrol = pg.app.controls.ZoomHistoryControl(navigcontrol)
        zoomhistcontrol.pack(fill='y', expand=1, side="right") #pack(fill='y', expand=1, side="right") #place(relx=0.02, rely=0.02, anchor="nw")
        mapview.add_control(zoomhistcontrol)

        #zoomcontrol = pg.app.controls.ZoomControl(navigcontrol)
        #zoomcontrol.pack(fill='y', expand=1, side="right") #pack(fill='y', expand=1, side="right") #place(relx=0.02, rely=0.02, anchor="nw")
        #mapview.add_control(zoomcontrol)

        ###########
        
        progbar = tk2.progbar.NativeProgressbar(mainframe)
        progbar.pack(side="left", padx=4, pady=4)

        def startprog():
            progbar.start()
        def stopprog():
            progbar.stop()
        mapview.onstart = startprog
        mapview.onfinish = stopprog

        coords = tk2.Entry(mainframe, width=30, state='readonly')
        coords.pack(side="right", padx=4, pady=4)

        def showcoords(event):
            x,y = mapview.mouse2coords(event.x, event.y)
            coords.set( "%s, %s" % (x,y) )
        self.mapview.bind("<Motion>", showcoords, "+")

        if False:#time:
            # must be dict
            timecontrol = pg.app.controls.TimeControl(mapview)#, **time)
            timecontrol.place(relx=0.5, rely=0.98, anchor="s")
            mapview.add_control(timecontrol)

        def dndfunc(event):
            for filepath in event.data:
                layerscontrol.add_layer(filepath)
        self.winfo_toplevel().bind_dnddrop(dndfunc, "Files", event='<Drop>')

        # done
        self.state('zoomed')

class MultiLayerGUI(tk2.Tk):
    # old working version
    def __init__(self, mapp, time=False, *args, **kwargs):
        tk2.basics.Tk.__init__(self, *args, **kwargs)

        self.ribbon = tk2.Ribbon(self)
        #self.ribbon.pack(fill="x", padx=15, pady=5)

        _hometab = self.ribbon.add_tab('Home')
        viewmode = tk2.Frame(_hometab, label="View Mode")
        viewmode.pack(side='left')
        mode2d = tk2.Button(viewmode)
        mode2d.set_icon(icons.iconpath('flatmap.jfif'), width=40, height=40)
        mode2d.pack(side='left')
        modelyr = tk2.Button(viewmode)
        modelyr.set_icon(icons.iconpath('layers.png'), width=40, height=40)
        modelyr.pack(side='left')
        mode3d = tk2.Button(viewmode)
        mode3d.set_icon(icons.iconpath('3d icon.png'), width=40, height=40)
        mode3d.pack(side='left')

        ###
        self.map = MultiLayerMap(self, mapp, time=time)
        self.map.pack(fill="both", expand=1)

        ###
##        _filtertab = self.ribbon.add_tab('Filters')
##        layers = tk2.scrollwidgets.OrderedList(_filtertab)
##        layers.pack(fill="both", expand=1)
##        def filter_options(widget):
##            widget.pack(fill="x", expand=1)
##
##            # left image/name part
##            left = tk2.Frame(widget)
##            left.pack(side="left")
##
##            #tkim = pg.app.icons.get('zoom_global.png', width=200, height=200)
##            lyr = widget.item
##            lyr.render(width=300, height=150)
##            im = lyr.img
##            lyr.img = None
##            print im, im.mode
##            import PIL, PIL.ImageTk
##            tkim = PIL.ImageTk.PhotoImage(im)
##            thumb = tk2.basics.Label(left, image=tkim)
##            thumb.tkim = tkim
##            thumb.pack(side="top")
##            
##            text = widget.item.data.name
##            if len(text) > 30:
##                text = "..."+text[-27:]
##            name = tk2.basics.Label(left, text=text)
##            name.pack(side="bottom")
##
##            # right paramaters and controls
##            right = tk2.Frame(widget)
##            right.pack(side="right")
##
##            dfilt = pg.app.controls.LayerFilterControl(right, layer=lyr)
##            dfilt.pack(side="left", fill="y", expand=1)
##            
##        for lyr in self.map.mapp.layers:
##            layers.add_item(lyr, filter_options)

        ###
##        _styletab = self.ribbon.add_tab('Styling')
##        layers = tk2.scrollwidgets.OrderedList(_styletab, title="Layer Styles:")
##        layers.pack(fill="both", expand=1)
##        def style_options(widget):
##            widget.pack(fill="x", expand=1)
##
##            # left image/name part
##            left = tk2.Frame(widget)
##            left.pack(side="left")
##
##            text = widget.item.data.name
##            if len(text) > 30:
##                text = "..."+text[-27:]
##            name = tk2.basics.Label(left, text=text)
##            name.pack(side="top")
##
##            #tkim = pg.app.icons.get('zoom_global.png', width=200, height=200)
##            import PIL, PIL.Image, PIL.ImageTk
##            lyr = widget.item
##            lyr.render(width=300, height=150, bbox=[lyr.bbox[0],lyr.bbox[3],lyr.bbox[2],lyr.bbox[1]])
##            im = lyr.img #.transform(lyr.img.size, PIL.Image.AFFINE, [1,0.9,0, 0,1,0, 0,0,1])
##            lyr.img = None
##            print im, im.mode
##            tkim = PIL.ImageTk.PhotoImage(im)
##            thumb = tk2.basics.Label(left, image=tkim)
##            thumb.tkim = tkim
##            thumb.pack(side="bottom")
##
##            # right paramaters and controls
##            right = tk2.Frame(widget)
##            right.pack(side="right", fill="y", expand=1)
##
##            _filtframe = tk2.Frame(right, label="Filtering")
##            _filtframe.pack(side="left", fill="y", expand=1)
##            dfilt = pg.app.controls.LayerFilterControl(_filtframe, layer=lyr)
##            dfilt.pack(side="top")
##
##            # fillcolor
##            _fillcolframe = tk2.Frame(right, label="Fillcolor")
##            _fillcolframe.pack(side="left", fill="y", expand=1)
##            _fillcoltypes = tk2.Ribbon(_fillcolframe)
##            _fillcoltypes.pack(side="left", fill="y", expand=1)
##            
##            _fillcolsingle = _fillcoltypes.add_tab("Single Color")
##            _ = tk2.Label(_fillcolsingle, text="Color")
##            _.pack(side="top") 
##            fillcol = tk2.ColorButton(_fillcolsingle)
##            fillcol.pack(side="top")
##            _ = tk2.Label(_fillcolsingle, text="Transparency")
##            _.pack(side="top") 
##            filltransp = tk2.Slider(_fillcolsingle)
##            filltransp.pack(side="top")
##
##            _fillcolgrad = _fillcoltypes.add_tab("Color Gradient")
##            fillcolbrk = tk2.Entry(_fillcolgrad, label="Gradient")
##            fillcolbrk.pack(side="top")
##            fillcolval = tk2.Entry(_fillcolgrad, label="Field Value")
##            fillcolval.pack(side="top")
##            fillcolbrk = tk2.Entry(_fillcolgrad, label="Value Breaks")
##            fillcolbrk.pack(side="top")
##            fillcolexc = tk2.Entry(_fillcolgrad, label="Exclude")
##            fillcolexc.pack(side="top")
##
##            _fillcolgrad = _fillcoltypes.add_tab("Categories")
##            fillcolbrk = tk2.Entry(_fillcolgrad, label="Colors")
##            fillcolbrk.pack(side="top")
##            fillcolval = tk2.Entry(_fillcolgrad, label="Field Value")
##            fillcolval.pack(side="top")
##            fillcolexc = tk2.Entry(_fillcolgrad, label="Exclude")
##            fillcolexc.pack(side="top")
##
##            # initiate with styleoptions
##            realfillcol = lyr.styleoptions.get('fillcolor')
##            if realfillcol:
##                if isinstance(realfillcol, dict):
##                    # breaks
##                    if realfillcol['breaks'] == 'unique':
##                        # ...
##                        _fillcoltypes.switch(tabname="Categories")
##                    else:
##                        # ...
##                        _fillcoltypes.switch(tabname="Color Gradient")
##                else:
##                    fillcol.set_color(realfillcol[:3])
##                    _fillcoltypes.switch(tabname="Single Color")
##            
##        for lyr in reversed(self.map.mapp.layers):
##            layers.add_item(lyr, style_options)
##
##        ###
##        self.ribbon.switch(tabname='Map')
                        
        self.state('zoomed')

# move below to "widgets.py"..?

class MultiLayerMap(tk2.basics.Label):
    def __init__(self, master, mapp, time=False, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.mapp = mapp

        mapview = self.mapview = pg.app.map.MapView(self, mapp)
        mapview.pack(fill="both", expand=1)

        layerscontrol = pg.app.controls.LayersControl(mapview)
        layerscontrol.layers = mapp.layers
        layerscontrol.place(relx=0.99, rely=0.02, anchor="ne")
        mapview.add_control(layerscontrol)

        navigcontrol = pg.app.controls.NavigateControl(mapview)
        navigcontrol.place(relx=0.5, rely=0.02, anchor="n")
        mapview.add_control(navigcontrol)

        identcontrol = pg.app.controls.IdentifyControl(navigcontrol)
        identcontrol.pack(fill='y', expand=1, side="right") #place(relx=0.98, rely=0.11, anchor="ne")
        mapview.add_control(identcontrol)

        zoomcontrol = pg.app.controls.ZoomControl(mapview)
        zoomcontrol.place(relx=0.01, rely=0.02, anchor="nw") #pack(fill='y', expand=1, side="right") #place(relx=0.02, rely=0.02, anchor="nw")
        mapview.add_control(zoomcontrol)

        #bottom = tk2.Label(self)
        #bottom.pack(fill="x", expand=1)
        
        progbar = tk2.progbar.NativeProgressbar(self)
        progbar.pack(side="left", padx=4, pady=4)

        def startprog():
            progbar.start()
        def stopprog():
            progbar.stop()
        mapview.onstart = startprog
        mapview.onfinish = stopprog

        coords = tk2.Label(self)
        coords.pack(side="right", padx=4, pady=4)

        def showcoords(event):
            x,y = mapview.mouse2coords(event.x, event.y)
            coords["text"] = "%s, %s" % (x,y)
        self.winfo_toplevel().bind("<Motion>", showcoords, "+")

        if False:#time:
            # must be dict
            timecontrol = pg.app.controls.TimeControl(mapview)#, **time)
            timecontrol.place(relx=0.5, rely=0.98, anchor="s")
            mapview.add_control(timecontrol)

        def dndfunc(event):
            for filepath in event.data:
                layerscontrol.add_layer(filepath)
        self.winfo_toplevel().bind_dnddrop(dndfunc, "Files", event='<Drop>')

class TableBrowser(tk2.basics.Label):
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.table = tk2.scrollwidgets.Table(self)
        self.table.pack(fill="both", expand=1)

        



