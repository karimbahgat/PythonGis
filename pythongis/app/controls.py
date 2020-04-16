
import os
import tk2

import pythongis as pg
from . import dialogs
from . import builder
from . import icons


class LayersControl(tk2.basics.Label):
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.layersbut = tk2.basics.Button(self)
        self.layersbut["command"] = self.toggle_layers
        self.layersbut.set_icon(icons.iconpath("layers.png"), width=40, height=40)
        self.layersbut.pack()

        self.layers = []

        w = self
        while w.master:
            w = w.master
        self._root = w
        self.layerslist = tk2.scrollwidgets.OrderedList(self._root, title="Map Layers:")

    def toggle_layers(self):
        if self.layerslist.winfo_ismapped():
            self.hide_layers()
        else:
            self.show_layers()

    def show_layers(self):
        for w in self.layerslist.items:
            w.destroy()
        for lyr in reversed(self.layers):
            self.layerslist.add_item(lyr, self.layer_decor)

        def ask_layer():
            filepath = tk2.filedialog.askopenfilename()
            self.add_layer(filepath)
        def buttondecor(w):
            but = tk2.Button(w, text="Add Layer", command=ask_layer)
            but.pack()
        self.layerslist.add_item(None, buttondecor)
        
        screenx,screeny = self.layersbut.winfo_rootx(),self.layersbut.winfo_rooty()
        x,y = screenx - self._root.winfo_rootx(), screeny - self._root.winfo_rooty()
        self.layerslist.place(anchor="ne", x=x, y=y, relheight=0.75) #, relwidth=0.9)

    def add_layer(self, filepath):
        # TODO: maybe open another dialogue where can set encoding, filtering, etc, before adding
        datawin = dialogs.LoadDataDialog(filepath=filepath)
        def onsuccess(data):
            # TODO: should prob be threaded...
            lyr = self.mapview.renderer.add_layer(data)
            self.mapview.renderer.render_one(lyr)
            self.mapview.renderer.update_draworder()
            self.mapview.update_image()
        datawin.onsuccess = onsuccess

    def hide_layers(self):
        self.layerslist.place_forget()

##    def layer_decor(self, widget):
##        """
##        Default way to decorate each layer with extra widgets
##        Override method to customize. 
##        """
##        widget.pack(fill="x", expand=1)
##        
##        visib = tk2.basics.Checkbutton(widget)
##        visib.select()
##        def toggle():
##            lyr = widget.item
##            lyr.visible = not lyr.visible
##            if lyr.visible:
##                self.mapview.renderer.render_one(lyr)
##            self.mapview.renderer.update_draworder()
##            self.mapview.update_image()
##        visib["command"] = toggle
##        visib.pack(side="left")
##        
##        text = widget.item.data.name
##        if len(text) > 50:
##            text = "..."+text[-47:]
##        name = tk2.basics.Label(widget, text=text)
##        name.pack(side="left", fill="x", expand=1)
##        
##        def browse():
##            from . import builder
##            win = tk2.Window()
##            win.state('zoom')
##            browser = builder.TableBrowser(win)
##            browser.pack(fill="both", expand=1)
##            lyr = widget.item
##            fields = lyr.data.fields
##            rows = (feat.row for feat in lyr.features()) # respects the filter
##            browser.table.populate(fields, rows)
##            
##        browse = tk2.basics.Button(widget, text="Browse", command=browse)
##        browse.pack(side="right")


    def layer_decor(self, widget):
        """
        Default way to decorate each layer with extra widgets
        Override method to customize. 
        """
        widget.pack(fill="x", expand=1)


        # left image/name part
        left = tk2.Frame(widget)
        left.pack(side="left")

        #tkim = pg.app.icons.get('zoom_global.png', width=200, height=200)
        import PIL, PIL.Image, PIL.ImageTk
        lyr = widget.item
        #lyr.render(width=300, height=150, bbox=[lyr.bbox[0],lyr.bbox[3],lyr.bbox[2],lyr.bbox[1]])
        w,h = self.mapview.renderer.width, self.mapview.renderer.height
        w,h = w/4, h/4
        if lyr.img:
            im = lyr.img.resize((w,h), resample=PIL.Image.BILINEAR) #.transform(lyr.img.size, PIL.Image.AFFINE, [1,0.9,0, 0,1,0, 0,0,1])
            tkim = PIL.ImageTk.PhotoImage(im)
        else:
            tkim = icons.get('zoom_global.png', width=w, height=h)
        thumb = tk2.basics.Label(left, image=tkim)
        thumb.tkim = tkim
        thumb.pack(side="bottom")

        i = len(self.mapview.renderer.layers) - self.mapview.renderer.layers.get_position(lyr)
        laynum = tk2.Label(left, text=i)
        laynum.pack(side="left")
    
        visib = tk2.basics.Checkbutton(left)
        visib.select()
        def toggle():
            lyr = widget.item
            lyr.visible = not lyr.visible
            if lyr.visible:
                self.mapview.renderer.render_one(lyr)
            self.mapview.renderer.update_draworder()
            self.mapview.update_image()
        visib["command"] = toggle
        visib.pack(side="left")
        
        text = widget.item.data.name
        if len(text) > 30:
            text = "..."+text[-27:]
        name = tk2.basics.Label(left, text=text)
        name.pack(side="left", fill="x", expand=1)        

        # right paramaters and controls
        right = tk2.Frame(widget)
        right.pack(side="right", fill="y", expand=1)

        _datframe = tk2.Frame(right, label="Data")
        _datframe.pack(side="left", fill="y", expand=1)
        dfilt = pg.app.controls.LayerFilterControl(_datframe, layer=lyr)
        dfilt.pack(side="top")
        def browse():
            from . import builder
            win = tk2.Window()
            win.state('zoom')
            browser = builder.TableBrowser(win)
            browser.pack(fill="both", expand=1)
            lyr = widget.item
            fields = lyr.data.fields
            rows = (feat.row for feat in lyr.features()) # respects the filter
            browser.table.populate(fields, rows)
        browse = tk2.basics.Button(_datframe, text="Browse Dataset", command=browse)
        browse.pack(pady=20)

        # fillcolor
        _fillcolframe = tk2.Frame(right, label="Fillcolor")
        _fillcolframe.pack(side="left", fill="y", expand=1)
        _fillcoltypes = tk2.Ribbon(_fillcolframe)
        _fillcoltypes.pack(side="left", fill="y", expand=1)
        
        _fillcolsingle = _fillcoltypes.add_tab("Single Color")
        _ = tk2.Label(_fillcolsingle, text="Color")
        _.pack(side="top") 
        fillcol = tk2.ColorButton(_fillcolsingle)
        fillcol.pack(side="top")
        _ = tk2.Label(_fillcolsingle, text="Transparency")
        _.pack(side="top") 
        filltransp = tk2.Slider(_fillcolsingle)
        filltransp.pack(side="top")

        _fillcolgrad = _fillcoltypes.add_tab("Color Gradient")
        fillcolbrk = tk2.Entry(_fillcolgrad, label="Gradient")
        fillcolbrk.pack(side="top")
        fillcolval = tk2.Entry(_fillcolgrad, label="Attribute")
        fillcolval.pack(side="top")
        fillcolbrk = tk2.Entry(_fillcolgrad, label="Breaks")
        fillcolbrk.pack(side="top")
        fillcolexc = tk2.Entry(_fillcolgrad, label="Exclude")
        fillcolexc.pack(side="top")

        _fillcolgrad = _fillcoltypes.add_tab("Categories")
        fillcolbrk = tk2.Entry(_fillcolgrad, label="Colors")
        fillcolbrk.pack(side="top")
        fillcolval = tk2.Entry(_fillcolgrad, label="Attribute")
        fillcolval.pack(side="top")
        fillcolexc = tk2.Entry(_fillcolgrad, label="Exclude")
        fillcolexc.pack(side="top")

        # initiate with styleoptions
        realfillcol = lyr.styleoptions.get('fillcolor')
        if realfillcol:
            if isinstance(realfillcol, dict):
                # breaks
                if realfillcol['breaks'] == 'unique':
                    # ...
                    _fillcoltypes.switch(tabname="Categories")
                else:
                    # ...
                    _fillcoltypes.switch(tabname="Color Gradient")
            else:
                fillcol.set_color(realfillcol[:3])
                _fillcoltypes.switch(tabname="Single Color")

    def move_layer(self):
        pass

class StaticLayersControl(tk2.basics.Label):
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.layers = []

        self.layerslist = tk2.scrollwidgets.OrderedList(self, title="Map Layers:")
        self.layerslist.pack(fill='both', expand=1)

        self.clickbind = self.winfo_toplevel().bind('<Button-1>', self.begin_drag, '+')

    def set_layers(self, layers):
        self.layers = layers
        self.update_layers()
        
##        def keep_updating():
##            # TODO: NOT IDEAL, ALOT OF WASTE, BETTER TO LISTEN FOR CHANGES? 
##            self.update_layers()
##            self.after(1000, keep_updating)
##        self.after(1000, keep_updating)

    def add_layer(self, filepath):
        # TODO: maybe open another dialogue where can set encoding, filtering, etc, before adding
        datawin = dialogs.LoadDataDialog(filepath=filepath)
        def onsuccess(data):
            # TODO: should prob be threaded...
            lyr = self.mapview.renderer.add_layer(data)
            self.mapview.renderer.render_one(lyr)
            self.mapview.renderer.update_draworder()
            self.mapview.update_image()
            self.update_layers()
        datawin.onsuccess = onsuccess

    def move_layer(self, layer, i):
        fromi = self.layers.get_position(layer)
        if fromi != i:
            self.layers.move_layer(fromi, i)
            self.update_layers()

    def remove_layer(self, layer):
        self.layers.remove_layer(self.layers.get_position(layer))
        self.update_layers()

    def update_layers(self):
        for w in self.layerslist.items:
            w.destroy()
        self.layerslist.items = []
        for lyr in reversed(self.layers):
            self.layerslist.add_item(lyr, self.layer_decor)

        def ask_layer():
            filepath = tk2.filedialog.askopenfilename()
            self.add_layer(filepath)
        def buttondecor(w):
            but = tk2.Button(w, text="Add Layer", command=ask_layer)
            but.pack()
        self.layerslist.add_item(None, buttondecor)

    def begin_drag(self, event):
        #print 'begin drag',event
        rootx,rooty = self.winfo_pointerxy()
        #print rootx,rooty
        for w in self.layerslist.items[:-1]:
            x1,y1 = w.winfo_rootx(), w.winfo_rooty()
            width,height = w.winfo_width(), w.winfo_height()
            x2,y2 = x1+width, y1+height
            #print x1,y1,x2,y2
            if x1 <= rootx <= x2 and y1 <= rooty <= y2:
                # this is the layer widget that was clicked
                #print 'found'
                self.clickwidget = w
                #self.followbind = self.winfo_toplevel().bind('<Motion>', self.follow_mouse, '+')
                self.releasebind = self.winfo_toplevel().bind('<ButtonRelease-1>', self.stop_drag, '+')
                break

    def follow_mouse(self, event):
        # gets called for entire app, so check to see if directly on canvas widget
        rootx,rooty = self.winfo_pointerxy()
        widgetx,widgety = self.layerslist.winfo_rootx(), self.layerslist.winfo_rooty()
        x,y = rootx-widgetx, rooty-widgety
        #print 'following',y
        #self.clickwidget.place(y=y)
        
    def stop_drag(self, event):
        rootx,rooty = self.winfo_pointerxy()
        #print 'stop drag',rooty
        i = 0
        for i,w in enumerate(self.layerslist.items[:-1]):
            widgetbottom = w.winfo_rooty() + w.winfo_height()
            #print rooty, widgetbottom, '-->', i
            if rooty < widgetbottom:
                #print 'found'
                break
        lyr = self.clickwidget.item
        i = len(self.layers) - 1 - i
        #print 'oldi',self.layers.get_position(lyr),'newi', i
        #self.winfo_toplevel().unbind('<Motion>', self.followbind)
        self.winfo_toplevel().unbind('<ButtonRelease-1>', self.releasebind)
        self.move_layer(lyr, i)

    def layer_decor(self, widget):
        """
        Default way to decorate each layer with extra widgets
        Override method to customize. 
        """
        widget.pack(fill="x", expand=1)

        frame = tk2.Frame(widget)
        frame.pack(fill='both', expand=1)

        # top name part
        nameframe = tk2.Label(frame)
        nameframe.pack(side="top")

        # middle image part
        imframe = tk2.Label(frame)
        imframe.pack(side="top")
        #tkim = pg.app.icons.get('zoom_global.png', width=200, height=200)
        import PIL, PIL.Image, PIL.ImageTk
        lyr = widget.item
        #lyr.render(width=300, height=150, bbox=[lyr.bbox[0],lyr.bbox[3],lyr.bbox[2],lyr.bbox[1]])
        w,h = self.mapview.renderer.width, self.mapview.renderer.height
        w,h = w//6, h//6
        if lyr.img:
            im = lyr.img.resize((w,h), resample=PIL.Image.BILINEAR) #.transform(lyr.img.size, PIL.Image.AFFINE, [1,0.9,0, 0,1,0, 0,0,1])
            tkim = PIL.ImageTk.PhotoImage(im)
        else:
            tkim = icons.get('zoom_global.png', width=h, height=h)
        thumb = tk2.basics.Label(imframe, image=tkim)
        thumb.tkim = tkim
        thumb.pack(side="bottom")

        i = len(self.mapview.renderer.layers) - self.mapview.renderer.layers.get_position(lyr)
        laynum = tk2.Label(nameframe, text=i)
        laynum.pack(side="left")
    
        visib = tk2.basics.Checkbutton(nameframe)
        visib.select()
        def toggle():
            lyr = widget.item
            lyr.visible = not lyr.visible
            if lyr.visible:
                self.mapview.renderer.render_one(lyr)
            self.mapview.renderer.update_draworder()
            self.mapview.update_image()
        visib["command"] = toggle
        visib.pack(side="left")
        
        text = widget.item.data.name
        text = text.replace('\\','/').split('/')[-1] # in case of path
        name = tk2.basics.Label(nameframe, text=text, width=20, wraplength=115)
        name.pack(side="left", fill="x", expand=1)
        zoombut = tk2.basics.Button(nameframe, command=lambda: self.mapview.zoom_bbox(lyr.bbox, log=True))
        zoombut.set_icon(icons.iconpath("zoom_rect.png"), width=15, height=15)
        zoombut.pack(side='left')
        confbut = tk2.basics.Button(nameframe)
        confbut.set_icon(icons.iconpath("config2.png"), width=15, height=15)
        confbut.pack(side='left')
        def delete():
            self.remove_layer(lyr)
        dropbut = tk2.basics.Button(nameframe, command=delete)
        dropbut.set_icon(icons.iconpath("delete.png"), width=15, height=15)
        dropbut.pack(side='left')

        transpframe = tk2.Label(frame)
        transpframe.pack(side="top")
        #transplabel = tk2.Label(transpframe, text="Transparency")
        #transplabel.pack(side="left")
        
        def update_transp(value):
            value = float(value) / 5.0
            lyr = widget.item
            lyr.transparency = value
            if lyr.visible:
                self.mapview.renderer.render_one(lyr)
            self.mapview.renderer.update_draworder()
            self.mapview.update_image()
            
        transp = tk2.Slider(transpframe, from_=0, to=5,
                            value=widget.item.transparency,
                            command=update_transp)
        transp.pack(side="right")
        

class NavigateControl(tk2.basics.Label):
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.zoomglob = tk2.basics.Button(self)
        self.zoomglob["command"] = lambda: self.mapview.zoom_global(log=True)
        self.zoomglob.set_icon(icons.iconpath("zoom_global.png"), width=40, height=40)
        self.zoomglob.pack(side="left")

        self.zoomrect = tk2.basics.Button(self)
        self.zoomrect["command"] = lambda: self.mapview.zoom_rect() # log is true by default
        self.zoomrect.set_icon(icons.iconpath("zoom_rect.png"), width=40, height=40)
        self.zoomrect.pack(side="left")

class ZoomHistoryControl(tk2.basics.Label):
    # not finished yet
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.prevbut = tk2.basics.Button(self, text='<')
        self.prevbut["command"] = lambda: self.mapview.zoom_previous()
        self.prevbut.set_icon(icons.iconpath("arrow_left.png"), width=40, height=40)
        self.prevbut.pack(side="left")

        self.nextbut = tk2.basics.Button(self, text='>')
        self.nextbut["command"] = lambda: self.mapview.zoom_next()
        self.nextbut.set_icon(icons.iconpath("arrow_right.png"), width=40, height=40)
        self.nextbut.pack(side="right")

class ZoomControl(tk2.basics.Label):
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.zoomin = tk2.basics.Button(self)#, height=40)
        self.zoomin.set_icon(icons.iconpath('plus.png'), width=22, height=22)
        self.zoomin["command"] = lambda: self.mapview.zoom_in()
        self.zoomin["text"] = u"\u2795" #"+"
        self.zoomin.pack(fill='y', expand=1, side='top')

        self.zoomout = tk2.basics.Button(self)#, height=40)
        self.zoomout.set_icon(icons.iconpath('minus.ico'), width=22, height=22)
        self.zoomout["command"] = lambda: self.mapview.zoom_out()
        self.zoomout["text"] = u"\u2796" #"-"
        self.zoomout.pack(fill='y', expand=1, side='bottom')

class MeasureControl(tk2.basics.Label):
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.measurebut = tk2.basics.Button(self, command=self.activate_measure)
        self.measurebut.set_icon(icons.iconpath("measure.png"), width=40, height=40)
        self.measurebut.pack()

        self.mouseicon_tk = icons.get("measure.png", width=30, height=30)

        self.measure_from = None
        self.measure_to = None

    def activate_measure(self):
        print "begin measure..."
        # replace mouse with identicon
        self.mouseicon_on_canvas = self.mapview.create_image(-100, -100, anchor="center", image=self.mouseicon_tk )
        #self.mapview.config(cursor="none")
        def follow_mouse(event):
            curx,cury = self.mapview.canvasx(event.x) + 28, self.mapview.canvasy(event.y) + 5
            self.mapview.coords(self.mouseicon_on_canvas, curx, cury)
        self.followbind = self.mapview.bind('<Motion>', follow_mouse, '+')
        # identify once clicked
        def callmeasure(event):
            # find
            curx,cury = self.mapview.canvasx(event.x), self.mapview.canvasy(event.y)
            self.measure_start(curx, cury)
        self.clickbind = self.winfo_toplevel().bind("<ButtonRelease-1>", callmeasure, "+")
        # cancel with esc button
        def cancel(event=None):
            self.mapview.unbind('<Motion>', self.followbind)
            self.winfo_toplevel().unbind('<ButtonRelease-1>', self.clickbind)
            self.winfo_toplevel().unbind('<Escape>', self.cancelbind)
            #self.mapview.config(cursor="arrow")
            self.mapview.delete(self.mouseicon_on_canvas)
        self.cancelbind = self.winfo_toplevel().bind("<Escape>", cancel, "+")

    def measure_start(self, x, y):
        print "measure start: ",x, y
        self.measure_from = (x,y)
        self.line = self.mapview.create_line(x, y, x, y, fill='black', width=2)

        # draw line from start to mouse
        def update_line(event):
            # gets called for entire app, so check to see if directly on canvas widget
            startx,starty = self.measure_from
            curx,cury = self.mapview.canvasx(event.x), self.mapview.canvasy(event.y)
            self.mapview.coords(self.line, startx, starty, curx, cury)
        self.followbind = self.mapview.bind('<Motion>', update_line, '+')
        def stopmeasure(event):
            # find
            curx,cury = self.mapview.canvasx(event.x), self.mapview.canvasy(event.y)
            self.measure_end(curx, cury)
        self.winfo_toplevel().unbind('<ButtonRelease-1>', self.clickbind)
        self.clickbind = self.winfo_toplevel().bind("<ButtonRelease-1>", stopmeasure, "+")

    def measure_end(self, x, y):
        print 'measure stop', x, y
        self.measure_to = (x,y)

        # update final line
        startx,starty = self.measure_from
        stopx,stopy = self.measure_to
        self.mapview.coords(self.line, startx, starty, stopx, stopy)

        # get as map coords
        _from = self.mapview.mouse2coords(startx, starty)
        _to = self.mapview.mouse2coords(stopx, stopy)

        # convert to latlon
        # for now assume already is...
        # ...

        # calc distance
        fromgeo = pg.vector.geography.Geography({'type':'Point', 'coordinates':_from})
        togeo = pg.vector.geography.Geography({'type':'Point', 'coordinates':_to})
        km = fromgeo.distance(togeo)

        def cancel(event=None):
            self.mapview.unbind('<Motion>', self.followbind)
            self.winfo_toplevel().unbind('<ButtonRelease-1>', self.clickbind)
            self.winfo_toplevel().unbind('<Escape>', self.cancelbind)
            #self.mapview.config(cursor="arrow")
            self.mapview.delete(self.mouseicon_on_canvas)
            self.mapview.delete(self.line)

        cancel()

        # report back
        msg = '''
From point: {}
To point: {}
Distance: {} km.'''.format(_from, _to, km)
        print msg
        tk2.messagebox.showinfo(title='Distance Measurement',
                                message=msg)

class IdentifyControl(tk2.basics.Label):
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.identifybut = tk2.basics.Button(self, command=self.begin_identify)
        self.identifybut.set_icon(icons.iconpath("identify.png"), width=40, height=40)
        self.identifybut.pack()

        self.mouseicon_tk = icons.get("identify.png", width=30, height=30)

    def begin_identify(self):
        print "begin identify..."
        # replace mouse with identicon
        self.mouseicon_on_canvas = self.mapview.create_image(-100, -100, anchor="center", image=self.mouseicon_tk )
        #self.mapview.config(cursor="none")
        def follow_mouse(event):
            # gets called for entire app, so check to see if directly on canvas widget
            root = self.winfo_toplevel()
            rootxy = root.winfo_pointerxy()
            mousewidget = root.winfo_containing(*rootxy)
            if mousewidget == self.mapview:
                curx,cury = self.mapview.canvasx(event.x) + 28, self.mapview.canvasy(event.y) + 5
                self.mapview.coords(self.mouseicon_on_canvas, curx, cury)
        self.followbind = self.winfo_toplevel().bind('<Motion>', follow_mouse, '+')
        # identify once clicked
        def callident(event):
            # reset
            cancel()
            # find
            x,y = self.mapview.mouse2coords(event.x, event.y)
            self.identify(x, y)
        self.clickbind = self.winfo_toplevel().bind("<ButtonRelease-1>", callident, "+")
        # cancel with esc button
        def cancel(event=None):
            self.winfo_toplevel().unbind('<Motion>', self.followbind)
            self.winfo_toplevel().unbind('<ButtonRelease-1>', self.clickbind)
            self.winfo_toplevel().unbind('<Escape>', self.cancelbind)
            #self.mapview.config(cursor="arrow")
            self.mapview.delete(self.mouseicon_on_canvas)
        self.cancelbind = self.winfo_toplevel().bind("<Escape>", cancel, "+")

    def identify(self, x, y):
        print "identify: ",x, y
        infowin = tk2.Window()
        infowin.wm_geometry("500x300")
        #infowin.state('zoomed')

        title = tk2.Label(infowin, text="Hits for coordinates: %s, %s" % (x, y))
        title.pack(fill="x")#, expand=1)
        
        ribbon = tk2.Ribbon(infowin)
        ribbon.pack(fill="both", expand=1)

        # find coord distance for approx 5 pixel uncertainty
        pixelbuff = 10
        p1 = self.mapview.renderer.pixel2coord(0, 0)
        p2 = self.mapview.renderer.pixel2coord(pixelbuff, 0)
        coorddist = self.mapview.renderer.drawer.measure_dist(p1, p2)

        # create uncertainty buffer around clickpoint
        from shapely.geometry import Point
        p = Point(x, y).buffer(coorddist)
        
        anyhits = None
        for layer in self.mapview.renderer.layers:
            if not layer.visible:
                continue
            print layer
            if isinstance(layer.data, pg.VectorData):
                feats = [feat for feat in layer.data.quick_overlap(p.bounds) if feat.get_shapely().intersects(p)]
                
                if feats:
                    anyhits = True
                    shortname = layer.data.name.replace('\\','/').split('/')[-1] # in case of path
                    _tab = ribbon.add_tab(shortname)
                    _frame = tk2.Frame(_tab, label=layer.data.name)
                    _frame.pack(fill='both', expand=1)
                    
                    browser = builder.TableBrowser(_frame)
                    browser.pack(fill="both", expand=1)
                    browser.table.populate(fields=layer.data.fields, rows=[f.row for f in feats])
                    
            elif isinstance(layer.data, pg.RasterData):
                values = [layer.data.get(x, y, band).value for band in layer.data.bands]
                if any((v != None for v in values)):
                    anyhits = True
                    shortname = layer.data.name.replace('\\','/').split('/')[-1] # in case of path
                    _tab = ribbon.add_tab(shortname)
                    _frame = tk2.Frame(_tab, label=layer.data.name)
                    _frame.pack(fill='both', expand=1)
                    
                    col,row = layer.data.geo_to_cell(x, y)
                    cellcol = tk2.Label(_frame, text="Column: %s" % col )
                    cellcol.pack(fill="x", expand=1)
                    cellrow = tk2.Label(_frame, text="Row: %s" % row )
                    cellrow.pack(fill="x", expand=1)

                    for bandnum,val in enumerate(values):
                        text = "Band %i: \n\t%s" % (bandnum, val)
                        valuelabel = tk2.Label(_frame, text=text)
                        valuelabel.pack(fill="both", expand=1)

        if not anyhits:
            infowin.destroy()

class DrawPolyControl(tk2.basics.Label):
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.drawbut = tk2.basics.Button(self, command=self.activate_draw)
        self.drawbut.set_icon(icons.iconpath("draw.png"), width=40, height=40)
        self.drawbut.pack()

        self.okbut = tk2.basics.Button(self, command=self.accept)
        self.okbut.set_icon(icons.iconpath("accept.png"), width=40, height=40)

        self.cancelbut = tk2.basics.Button(self, command=self.cancel)
        self.cancelbut.set_icon(icons.iconpath("delete.png"), width=40, height=40)

        self.mouseicon_tk = icons.get("draw.png", width=30, height=30)

        self.draw_geoj = {'type':'MultiPolygon', 'coordinates':[]}
        self.draw_ids = []

    def activate_draw(self):
        print "begin draw poly..."
        # replace mouse with identicon
        self.mouseicon_on_canvas = self.mapview.create_image(-100, -100, anchor="center", image=self.mouseicon_tk )
        def follow_mouse(event):
            curx,cury = self.mapview.canvasx(event.x) + 28, self.mapview.canvasy(event.y) + 5
            self.mapview.coords(self.mouseicon_on_canvas, curx, cury)
        self.followbind = self.mapview.bind('<Motion>', follow_mouse, '+')

        # hide draw button and show accept/cancel button
        self.drawbut.pack_forget()
        self.okbut.pack(side='right')
        self.cancelbut.pack(side='right')
        
        # update geom
        def update_geom(event):
            # gets called for entire app, so check to see if directly on canvas widget
            if not self.draw_ids or len(self.draw_ids) != len(self.draw_geoj['coordinates']):
                return
            for drawid,poly in zip(self.draw_ids, self.draw_geoj['coordinates'][:len(self.draw_ids)]):
                coords = list(poly[0]) # exterior only
                # at least 3 vertices
                while len(coords) < 3:
                    coords.append(coords[-1])
                # convert to canvas coords
                coords = [self.mapview.renderer.drawer.coord2pixel(*p) for p in coords]
                # add current mouse pos if last shape
                if drawid == self.draw_ids[-1]:
                    curx,cury = self.mapview.canvasx(event.x), self.mapview.canvasy(event.y)
                    coords.append((curx,cury))
                # update
                coords_flat = [x_or_y for p in coords for x_or_y in p]
                self.mapview.coords(drawid, *coords_flat)
        self.followbind = self.mapview.bind('<Motion>', update_geom, '+')
        
        # draw once clicked
        def calldraw(event):
            # find
            curx,cury = self.mapview.canvasx(event.x), self.mapview.canvasy(event.y)
            curx,cury = self.mapview.renderer.pixel2coord(curx, cury)
            self.draw_vertice(curx, cury)
        self.clickbind = self.winfo_toplevel().bind("<ButtonRelease-1>", calldraw, "+")
        
        # finish with right click
        def callfinish(event):
            # find
            curx,cury = self.mapview.canvasx(event.x), self.mapview.canvasy(event.y)
            curx,cury = self.mapview.renderer.pixel2coord(curx, cury)
            self.draw_vertice(curx, cury)
            self.draw_finish()
        self.finishbind = self.winfo_toplevel().bind("<ButtonRelease-3>", callfinish, "+")
        
        # cancel with esc button
        def cancel(event=None):
            if self.draw_ids:
                self.mapview.delete(self.draw_ids.pop(-1)) # delete current canvas polygon
                self.draw_geoj['coordinates'][-1] = [] # empty out the current geoj
        self.cancelbind = self.winfo_toplevel().bind("<Escape>", cancel, "+")

    def draw_vertice(self, x, y):
        print "draw_vertice: ",x, y
        if not self.draw_geoj['coordinates']:
            self.draw_geoj['coordinates'].append([[]]) # add empty exterior
            
        curpoly = self.draw_geoj['coordinates'][-1]
        curpoly[0].append((x,y)) # add to exterior
        
        if len(curpoly[0]) == 1:
            # first vertice
            coords = list(curpoly[0]) # exterior
            while len(coords) < 3:
                coords.append(coords[-1])
            # convert to canvas coords
            coords = [self.mapview.renderer.drawer.coord2pixel(*p) for p in coords]
            # create drawid
            print 'create', coords
            coords_flat = [x_or_y for p in coords for x_or_y in p]
            drawid = self.mapview.create_polygon(*coords_flat, fill='blue', outline='black', stipple='gray50')
            self.draw_ids.append(drawid)

    def draw_finish(self):
        # complete the polygon (exterior)
        curpoly = self.draw_geoj['coordinates'][-1]
        curpoly[0].append(curpoly[0][0])
        print 'finish',curpoly[0]
        # add new empty polygon
        self.draw_geoj['coordinates'].append([[]])

    def accept(self):
        # check geoj
        geoj = self.draw_geoj
        geoj['coordinates'].pop(-1) # drop the latest one, either empty or unfinished
        if geoj['coordinates']:
            # make vectordata
            d = pg.VectorData()
            d.add_feature([], geoj)
            # add to renderer
            self.mapview.renderer.add_layer(d)
            for cntr in self.mapview.controls:
                if isinstance(cntr, StaticLayersControl):
                    cntr.update_layers()
        # exit draw mode
        self.cancel()

    def cancel(self):
        # hide accept/cancel button and show draw button
        self.okbut.pack_forget()
        self.cancelbut.pack_forget()
        self.drawbut.pack(side='right')

        # unbind events
        self.mapview.unbind('<Motion>', self.followbind)
        self.winfo_toplevel().unbind('<ButtonRelease-1>', self.clickbind)
        self.winfo_toplevel().unbind('<ButtonRelease-3>', self.finishbind)
        self.winfo_toplevel().unbind('<Escape>', self.cancelbind)
        #self.mapview.config(cursor="arrow")

        # delete stuff
        self.mapview.delete(self.mouseicon_on_canvas)
        for drawid in self.draw_ids:
            self.mapview.delete(drawid) # delete canvas polygon
        self.draw_geoj['coordinates'] = []
        self.draw_ids = []

class MapProjectionControl(tk2.basics.Label):
    def __init__(self, master, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.projbut = tk2.basics.Button(self)
        self.projbut["command"] = self.toggle_projections
        self.projbut.set_icon(icons.iconpath("projections.png"), width=40, height=40)
        self.projbut.pack()

        import pycrs
##        self.projections = [pycrs.parse.from_epsg_code(4326), # wgs84
##                            pycrs.parse.from_proj4(next(pycrs.utils.search_name('robinson'))['proj4']),
##                            pycrs.parse.from_proj4(next(pycrs.utils.search_name('mercator'))['proj4']),
##                            pycrs.parse.from_proj4(next(pycrs.utils.search_name('mollweide'))['proj4']),
##                            pycrs.parse.from_proj4(next(pycrs.utils.search_name('van der grinten'))['proj4']),
##                            pycrs.parse.from_proj4(next(pycrs.utils.search_name('eckert II'))['proj4']),
##                            pycrs.parse.from_proj4(next(pycrs.utils.search_name('eckert IV'))['proj4']),
##                            pycrs.parse.from_sr_code(6980), # space
##                            ]
        self.projections = ['+proj=longlat +datum=WGS84 +ellps=WGS84 +a=6378137.0 +rf=298.257223563 +pm=0 +nodef',
                            '+proj=robin +datum=WGS84 +ellps=WGS84 +a=6378137.0 +rf=298.257223563 +pm=0 +lon_0=0 +x_0=0 +y_0=0 +units=m +axis=enu +no_defs',
                            '+proj=merc +a=6370997 +b=6370997 +pm=0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k_0=1.0 +lat_ts=0.0 +units=m +axis=enu +no_defs',
                            '+proj=moll +datum=WGS84 +ellps=WGS84 +a=6378137.0 +rf=298.257223563 +pm=0 +lon_0=0 +x_0=0 +y_0=0 +units=m +axis=enu +no_defs',
                            '+proj=vandg +datum=WGS84 +ellps=WGS84 +a=6378137.0 +rf=298.257223563 +pm=0 +lon_0=0 +x_0=0 +y_0=0 +units=m +axis=enu +no_defs',
                            '+proj=eck4 +datum=WGS84 +ellps=WGS84 +a=6378137.0 +rf=298.257223563 +pm=0 +lon_0=0 +x_0=0 +y_0=0 +units=m +axis=enu +no_defs',
                            '+proj=ortho +a=6370997 +b=6370997 +pm=0 +lon_0=-72.53333333339999 +x_0=0 +y_0=0 +lat_0=42.5333333333 +units=m +axis=enu +no_defs',
                           ]
        self.projections = [pycrs.parse.from_proj4(proj4) for proj4 in self.projections]


        self.chosen = tk2.StringVar(self, value='')

        w = self
        while w.master:
            w = w.master
        self._root = w
        self.projlist = tk2.scrollwidgets.OrderedList(self._root, title="Map Projections:")

    def toggle_projections(self):
        if self.projlist.winfo_ismapped():
            self.hide_projections()
        else:
            self.show_projections()

    def show_projections(self):
        for w in self.projlist.items:
            w.destroy()
        self.projlist.items = []

        cur = self.mapview.renderer.crs
        self.chosen.set(cur)
        self.projlist.add_item(cur, self.proj_decor)
        curproj4 = cur.to_proj4()
        for proj in self.projections:
            if proj.to_proj4() == curproj4:
                continue
            self.projlist.add_item(proj, self.proj_decor)
        
        screenx,screeny = self.projbut.winfo_rootx(),self.projbut.winfo_rooty()
        x,y = screenx - self._root.winfo_rootx(), screeny - self._root.winfo_rooty()
        self.projlist.place(anchor="sw", x=x, y=y, relheight=0.75) #, relwidth=0.9)

    def hide_projections(self):
        self.projlist.place_forget()

    def proj_decor(self, widget):
        """
        Default way to decorate each layer with extra widgets
        Override method to customize. 
        """
        widget.pack(fill="x", expand=1)

        frame = tk2.Frame(widget)
        frame.pack(fill='both', expand=1)

        # top name part
        nameframe = tk2.Label(frame)
        nameframe.pack(side="top")

        # middle image part
        imframe = tk2.Label(frame)
        imframe.pack(side="top")
        #tkim = pg.app.icons.get('zoom_global.png', width=200, height=200)
        import PIL, PIL.Image, PIL.ImageTk
        lyr = widget.item
        #lyr.render(width=300, height=150, bbox=[lyr.bbox[0],lyr.bbox[3],lyr.bbox[2],lyr.bbox[1]])
        w,h = self.mapview.renderer.width, self.mapview.renderer.height
        w,h = w//6, h//6
        if self.mapview.renderer.img:
            im = self.mapview.renderer.img.resize((w,h), resample=PIL.Image.BILINEAR) #.transform(lyr.img.size, PIL.Image.AFFINE, [1,0.9,0, 0,1,0, 0,0,1])
            tkim = PIL.ImageTk.PhotoImage(im)
        else:
            tkim = icons.get('zoom_global.png', width=h, height=h)
        thumb = tk2.basics.Label(imframe, image=tkim)
        thumb.tkim = tkim
        thumb.pack(side="bottom")
    
        selector = tk2.basics.Radiobutton(nameframe, variable=self.chosen, value=widget.item)
        def choose():
            crs = widget.item
            self.chosen.set(crs) # update the var
            self.mapview.renderer.crs = crs
            self.mapview.renderer.zoom_auto()
            self.mapview.threaded_rendering()
            self.hide_projections()
        selector["command"] = choose
        selector.pack(side="left")
        imframe.bind('<Button-1>', lambda e: choose(), '+')
        thumb.bind('<Button-1>', lambda e: choose(), '+')

        if hasattr(widget.item, 'proj'):
            name = widget.item.proj.name.ogc_wkt
        else:
            name = widget.item.datum.name.ogc_wkt
        text = name
        text = text.replace('_', ' ')
        name = tk2.basics.Label(nameframe, text=text, width=20, wraplength=115)
        name.pack(side="left", fill="x", expand=1)
        confbut = tk2.basics.Button(nameframe)
        confbut.set_icon(icons.iconpath("config2.png"), width=15, height=15)
        confbut.pack(side='left')
        
class LayerFilterControl(tk2.basics.Label):
    def __init__(self, master, layer, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.layer = layer

        self.filterfield = tk2.Entry(self, label="Filter Expression", labelside="top") #tk2.texteditor.Text()
        self.filterfield.pack(side="top")

        #self.runbut = tk2.Button(self, text="Apply", command=self.run)
        #self.runbut.pack(side="bottom")

    def run(self):
        expr = self.filterfield.get()
        print expr
        filtfunc = eval('lambda f: %s' % expr)
        self.layer.datafilter = filtfunc

class FilterSliderControl(tk2.basics.Label):
    def __init__(self, master, fromval=0, toval=0, *args, **kwargs):
        tk2.basics.Label.__init__(self, master, *args, **kwargs)

        self.slider = tk2.Slider(self)
        self.slider.pack(fill="both", expand=1)

##    def gg
##        for lyr in self.mapview.layers:
##            alldates = key(f) for f in self.mapview.la
##
##        if not start:
##            start = min(

class InsetMapControl:
    def __init__(self, master, *args, **kwargs):
        pass




