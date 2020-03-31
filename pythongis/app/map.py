# Import builtins
import time
import Tkinter as tk
import tk2
import pythongis as pg
import os

from . import icons




# The Main Map

class MapView(tk.Canvas):
    def __init__(self, master, renderer, **kwargs):        
        # Make this class a subclass of tk.Canvas and add to it
        kwargs["bg"] = kwargs.get("bg", "#%02x%02x%02x" % (255,255,255)) #(111,111,111))
        tk.Canvas.__init__(self, master, **kwargs)
        self.renderer = renderer
        self.controls = []

        # Attributes
        self.onstart = None
        self.onsuccess = None
        self.onfinish = None
        self.onmousemove = None
        
        self.mousepressed = False
        self.mouse_mode = "pan"
        self.zoomcenter = None
        self.zoomfactor = 1
        self.zoomdir = None
        self.last_zoomed = None

        self.zoom_history = [self.renderer.bbox]
        self.zoom_cur = 0

        # Setup
        # link to self
        self.renderer.mapview = self
        # fill with blank image
        self.tkimg = None
        self.image_on_canvas = self.create_image(0, 0, anchor="nw", image=self.tkimg )
        
        # Schedule resize map on window resize
        self.last_resized = None
        def resizing(event):
            # record resize time
            self.last_resized = time.time()
            # schedule to check if finished resizing after x millisecs
            self.after(300, lambda: resize_if_finished(event))
            
        def resize_if_finished(event):
            # only if x time since last resize event
            if time.time() - self.last_resized > 0.3:
                self.last_resized = time.time()
                width, height = event.width, event.height #self.winfo_width(), self.winfo_height()
                self.renderer.resize(width, height)
                #self.renderer.width = width
                #self.renderer.height = height
                self.threaded_rendering()
        self.bind("<Configure>", resizing)
        
        # Bind interactive zoom events
        
        def doubleleft(event):
            self.zoomfactor += 1
            canvasx,canvasy = self.canvasx(event.x),self.canvasy(event.y)
            self.zoomcenter = self.renderer.pixel2coord(canvasx, canvasy)
            self.zoomdir = "in"
            # record zoom time
            self.last_zoomed = time.time()
            # schedule to check if finished zooming after x millisecs
            self.after(300, lambda: self.zoom_if_finished(log=True))

        def doubleright(event):
            self.zoomfactor += 1
            canvasx,canvasy = self.canvasx(event.x),self.canvasy(event.y)
            self.zoomcenter = self.renderer.pixel2coord(canvasx, canvasy)
            self.zoomdir = "out"
            # record zoom time
            self.last_zoomed = time.time()
            # schedule to check if finished zooming after x millisecs
            self.after(300, lambda: self.zoom_if_finished(log=True))

        def mousewheel(event):
            # FIX: since we bind to all, event coordinates are captured by root
            # so it seems these are not what canvasx/y expect, leading to wacky zooms... 
            d = event.delta
            #print event.x,event.y
            #event.x,event.y = self.winfo_pointerxy()
            #print event.x,event.y
            if d < 0:
                doubleright(event)
            else:
                doubleleft(event)

##        def zoom_if_finished():
##            if time.time() - self.last_zoomed >= 0.2:
##                # remember old bbox
##                oldbbox = list(self.renderer.drawer.coordspace_bbox)
##                # get new bbox from zoom
##                if self.zoomdir == "out":
##                    self.renderer.zoom_out(self.zoomfactor, center=self.zoomcenter)
##                else:
##                    self.renderer.zoom_in(self.zoomfactor, center=self.zoomcenter)
##
##                # render fresh
##                self.threaded_rendering(oldbbox)
##                # reset zoomfactor
##                self.zoomfactor = 1
##                self.last_zoomed = None

        self.bind("<Double-Button-1>", doubleleft)
        self.bind("<Double-Button-3>", doubleright)
        # Warning: had to bind to all, since wasn't firing on just the canvas,
        # so mousewheel will trigger zoom even when pointer outside the map
        #self.bind_all("<MouseWheel>", mousewheel)
        #self.bind_all("<Button-4>", mousewheel)
        #self.bind_all("<Button-5>", mousewheel)

        # bind interactive pan and rectangle-zoom events

        def mousepressed(event):
            if self.last_zoomed: return
            self.mousepressed = True
            self.startxy = self.canvasx(event.x), self.canvasy(event.y)
            #imx,imy = self.coords(self.image_on_canvas)
            #self.startxy = imx + self.startxy[0], imy + self.startxy[1]
            if self.mouse_mode == "zoom":
                startx,starty = self.startxy
                self.rect = self.create_rectangle(startx, starty, startx+1, starty+1, fill=None)

        def mousemoving(event):
            if self.onmousemove:
                # mouse coords
                self.onmousemove(event)
            if self.mouse_mode == "pan":
                if self.mousepressed:
                    startx,starty = self.startxy
                    curx,cury = self.canvasx(event.x), self.canvasy(event.y)
                    xmoved = curx - startx
                    ymoved = cury - starty
                    self.coords(self.image_on_canvas, xmoved, ymoved) # offset the image rendering
            elif self.mouse_mode == "zoom":
                curx,cury = self.canvasx(event.x), self.canvasy(event.y)
                self.coords(self.zoomicon_on_canvas, curx + 30, cury + 10)
                if self.mousepressed:
                    startx,starty = self.startxy
                    self.coords(self.rect, startx, starty, curx, cury)

        def mousereleased(event):
            if self.last_zoomed: return
            self.mousepressed = False
            if self.mouse_mode == "pan":
                startx,starty = self.startxy
                curx,cury = self.canvasx(event.x), self.canvasy(event.y)
                xmoved = int(curx - startx)
                ymoved = int(cury - starty)
                #print startx,starty,curx,cury,xmoved,ymoved
                #print 'pre move',self.renderer.bbox
                #print 'offset',xmoved,ymoved
                if xmoved or ymoved:
                    # offset image rendering
                    self.renderer.offset(xmoved, ymoved)
                    #print 'post move',self.renderer.bbox
                    # log it
                    self.log_zoom(self.renderer.bbox)
                    # since threaded rendering will update the offset image, reanchor the dragged canvas image
                    self.coords(self.image_on_canvas, 0, 0) # always reanchor rendered image nw at 0,0 in case of panning
                    # render
                    self.threaded_rendering() #update_image=False)
            elif self.mouse_mode == "zoom":
                startx,starty = self.startxy
                curx,cury = self.canvasx(event.x), self.canvasy(event.y)
                self.coords(self.rect, startx, starty, curx, cury)
                # disactivate rectangle selector
                self.delete(self.rect)
                self.event_generate("<Leave>") # fake a mouseleave event to destroy icon
                self.mouse_mode = "pan"
                # make the zoom
                startx,starty = self.renderer.drawer.pixel2coord(startx,starty)
                curx,cury = self.renderer.drawer.pixel2coord(curx,cury)
                bbox = [startx, starty, curx, cury]
                #self.rough_zoom_bbox(bbox)
                self.zoom_bbox(bbox, log=True)

        self.zoomicon_tk = icons.get("zoom_rect.png", width=30, height=30)
        def mouseenter(event):
            if self.mouse_mode == "zoom":
                # replace mouse with zoomicon
                self.zoomicon_on_canvas = self.create_image(event.x, event.y, anchor="center", image=self.zoomicon_tk )
                #self.config(cursor="none")

        def mouseleave(event):
            if self.mouse_mode == "zoom":
                # back to normal mouse
                self.delete(self.zoomicon_on_canvas)
                #self.config(cursor="arrow")

        def cancel(event):
            if self.mouse_mode == "zoom":
                self.event_generate("<Leave>") # fake a mouseleave event to destroy icon
                self.mouse_mode = "pan"
                if self.mousepressed:
                    self.delete(self.rect)

        # bind them
        self.bind("<Button-1>", mousepressed, "+")
        self.bind("<Motion>", mousemoving)
        self.bind("<ButtonRelease-1>", mousereleased, "+")
        self.bind("<Enter>", mouseenter)
        self.bind("<Leave>", mouseleave)
        self.winfo_toplevel().bind("<Escape>", cancel)

    def add_control(self, control):
        control.mapview = self
        self.controls.append(control)

    def log_zoom(self, bbox):
        if self.zoom_cur < len(self.zoom_history)-1:
            # branch off (forget all next ones)
            self.zoom_history = self.zoom_history[:self.zoom_cur+1]
        self.zoom_history.append(bbox)
        self.zoom_cur += 1
        #print 'logging zoom', self.zoom_cur, bbox, len(self.zoom_history), self.zoom_history

    def zoom_previous(self):
        if self.zoom_cur > 0:
            self.zoom_cur -= 1
            bbox = self.zoom_history[self.zoom_cur]
            #print 'previous zoom', self.zoom_cur, bbox, len(self.zoom_history), self.zoom_history
            self.zoom_bbox(bbox)

    def zoom_next(self):
        if self.zoom_cur < len(self.zoom_history)-1:
            self.zoom_cur += 1
            bbox = self.zoom_history[self.zoom_cur]
            #print 'next zoom', self.zoom_cur, bbox, len(self.zoom_history), self.zoom_history
            self.zoom_bbox(bbox)

    def zoom_global(self, log=False):
        # get new bbox
        globalbbox = self.renderer.layers.bbox(self.renderer.crs)
        self.renderer.zoom_bbox(*globalbbox)
        if log:
            self.log_zoom(globalbbox)
        # render fresh
        self.threaded_rendering()

    def zoom_rect(self):
        self.mouse_mode = "zoom"
        self.event_generate("<Enter>")

    def zoom_bbox(self, bbox, log=False):
        # get new bbox from zoom
        self.renderer.zoom_bbox(*bbox)
        if log:
            self.log_zoom(bbox)
        # fresh render
        self.threaded_rendering()

    def mouse2coords(self, x, y):
        px,py = self.canvasx(x), self.canvasy(y)
        x,y = self.renderer.pixel2coord(px, py)
        return x,y

    def threaded_rendering(self, update_image=True):
        # perform render/zoom in separate thread
        if self.onstart:
            self.onstart()
        print "rendering thread..."
        import time

##        if oldbbox:
##            # perform a fast cropzoom before rendering in full
##            t=time.time()
##            oldw,oldh = self.renderer.width,self.renderer.height
##            newbbox = list(self.renderer.drawer.coordspace_bbox)
##            # crop then resize existing image from oldbbox to newbbox
##            # get zoomratio by comparing old to new width
##            # ...although could also use height, both have same ratio due to
##            # ...zoom box should always be fitted inside window ratio
##            zoomratio = (oldbbox[2]-oldbbox[0]) / float(newbbox[2]-newbbox[0])
##            if zoomratio < 1:
##                # newbox is larger than oldbox, meaning zooms out
##                # so to avoid very large images from crop(), resize to smaller first
##                # we multiply by x to get slightly better quality
##                supersample = 1
##                self.renderer.resize(int(oldw*zoomratio*supersample), int(oldh*zoomratio*supersample))
##                print self.renderer.img
##            self.renderer.zoom_bbox(*oldbbox)
##            self.renderer.crop(*newbbox)
##            self.renderer.resize(oldw, oldh)
##            # update image
##            self.tkimg = self.renderer.get_tkimage()
##            self.itemconfig(self.image_on_canvas, image=self.tkimg )
##            self.update()
            #print "-cropzoom",time.time()-t

        # display zoomed image while waiting
        # previous zooms and changes to the view extent are already stored in the render img, just update it to the screen
        if update_image:
            self.update_image()

        # begin rendering thread
        t=time.time()
        pending = self.master.new_thread(self.renderer.render_all)

        def finish(result):
            if isinstance(result, Exception):
                tk2.messagebox.showerror(self, "Rendering error: " + str(result) )
            else:
                import time
                print "-threadrend",time.time()-t
                # update renderings
                
                self.coords(self.image_on_canvas, 0, 0) # always reanchor rendered image nw at 0,0 in case of panning
                self.update_image()
                # custom funcs
                if self.onsuccess:
                    self.onsuccess()
            # stop progbar
            if self.onfinish:
                self.onfinish()
            
        self.master.process_thread(pending, finish, mslag=1, msinterval=21) # faster checking/update of tk img

    def update_image(self):

        # direct image blit (windows only)
##        from PIL import ImageWin
##        t=time.time() 
##        dib=ImageWin.Dib(self.renderer.img)
##        hwnd = ImageWin.HWND(self.winfo_id())
##        dib.expose(hwnd)
##        self.bind("<Expose>", lambda e: dib.expose(hwnd))
##        print "-tkfresh",time.time()-t

        # tkimage update threadded
##        t=time.time()
##        pending = self.master.new_thread(self.renderer.get_tkimage)
##
##        def finish(result):
##            if isinstance(result, Exception):
##                tk2.messagebox.showerror(self, "Rendering error: " + str(result) )
##            else:
##                #import time
##                print "-tkfresh3",time.time()-t
##                # update renderings
##                self.tkimg = result
##                self.itemconfig(self.image_on_canvas, image=self.tkimg )
##        
##            # stop progbar
##            if self.onfinish:
##                self.onfinish()
##        print "-tkfresh",time.time()-t
##        self.master.process_thread(pending, finish, mslag=1, msinterval=121) # faster checking/update of tk img
##        print "-tkfresh2",time.time()-t

        # tkimage update
        if self.renderer.img:
            tt=time.time()
            self.tkimg = self.renderer.get_tkimage()
            print "-tkfresh",time.time()-tt
            self.itemconfig(self.image_on_canvas, image=self.tkimg )

    def zoom_in(self, log=False):
        self.zoomfactor += 1
        self.zoomcenter = None
        self.zoomdir = "in"
        # record zoom time
        self.last_zoomed = time.time()
        # schedule to check if finished zooming after x millisecs
        self.after(300, lambda log=log: self.zoom_if_finished(log=log))

    def zoom_out(self, log=False):
        self.zoomfactor += 1
        self.zoomcenter = None
        self.zoomdir = "out"
        # record zoom time
        self.last_zoomed = time.time()
        # schedule to check if finished zooming after x millisecs
        self.after(300, lambda log=log: self.zoom_if_finished(log=log))

    def zoom_if_finished(self, log=False):
        if time.time() - self.last_zoomed >= 0.3:
            # get new bbox from zoom
            if self.zoomdir == "out":
                self.renderer.zoom_out(self.zoomfactor, center=self.zoomcenter)
            else:
                self.renderer.zoom_in(self.zoomfactor, center=self.zoomcenter)

            if log:
                self.log_zoom(list(self.renderer.drawer.coordspace_bbox))

            # render fresh
            self.threaded_rendering()
            # reset zoomfactor
            self.zoomfactor = 1
            self.last_zoomed = None





