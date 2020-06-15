"""
Tk2
Wraps around all the major widgets
"""


# Imports

import sys
if sys.version.startswith("2"):
    import Tkinter as tk
    import Tkdnd as dnd
    import Queue
else:
    import tkinter as tk
    import tkinter.dnd as dnd
    import queue as Queue
import ttk

import threading
import traceback

from . import filednd





# Master inheriting overrides

def get_master(master):
    if hasattr(master, "interior"):
        master = master.interior
    return master





# Expanded binding methods

class BindMixin(object):
    def __init__(self, master=None, **kwargs):
        self._bindings = dict()

    # the expanded bind methods

    # TODO: Merge bind_until and bind_once into the normal bind method
    # ...by adding untilevent, untilexpires, and untilrepeat options,
    # ...thus combining multiple possible until-conditions.
    # ALSO: Make sure to overwrite any existing event names if specified
    # ...more than once. And make "+" the default behavior so dont have
    # ...to specify.

    # IMPLEMENT THIS INSTEAD MAYBE:
    # https://mail.python.org/pipermail//tkinter-discuss/2012-May/003152.html
    
    def bind(self, eventtype, eventfunc, add=None, bindname=None):
        bindid = super(BindMixin, self).bind(eventtype, eventfunc, add)
        if bindname:
            if not eventtype in self._bindings:
                self._bindings[eventtype] = dict()
            self._bindings[eventtype][bindname] = bindid
        return bindid  # because that is the old behavior, so as not to break

    def bind_until(self, eventtype, eventfunc, add=None, bindname=None, untilevent=None, untilexpires=None):
        bindid = super(BindMixin, self).bind(eventtype, eventfunc, add)
        if untilevent:
            def unbind(event):
                super(BindMixin, self).unbind(eventtype, bindid)
                super(BindMixin, self).unbind(untilevent, unbindid)
            unbindid = super(BindMixin, self).bind(untilevent, unbind)
        if untilexpires:
            self.after(untilexpires, lambda: self.unbind(eventtype, bindid) )
            if untilevent:
                super(BindMixin, self).unbind(untilevent, unbindid)

    def bind_once(self, eventtype, eventfunc, add=None):
        # doesnt work yet...
        def wrapfunc(event):
            eventfunc(event)
            super(BindMixin, self).unbind(eventtype, bindid)
        bindid = super(BindMixin, self).bind(eventtype, wrapfunc, add)
                
    def unbind(self, eventtype, bindid):
        if eventtype in self._bindings and bindid in self._bindings[eventtype]:
            bindid = self._bindings[eventtype].pop(bindid)
        super(BindMixin, self).unbind(eventtype, bindid)

        
    # rightclick

    def bind_rightclick(self, menuitems):
        """
        menuitems can be a sequence or a function for dynamic listing
        """

        def openmenu(event):
            menu = tk.Menu(self, tearoff=False)
            
            if hasattr(menuitems, "__call__"):
                realmenuitems = menuitems()

            else:
                realmenuitems = menuitems
            
            for item in realmenuitems:
                if len(item) == 2:
                    name,func = item
                    menu.add_command(label=name, command=func)
                elif len(item) == 3:
                    name,func,img = item
                    # maybe need to load the image? 
                    menu.add_command(label=name, command=func, image=img)

            menu.post(event.x_root, event.y_root)

        self.bind("<Button-3>", openmenu, "+", "rightclickmenu")

    def unbind_rightclick(self):
        self.unbind("<Button-3>", "rightclickmenu")

    # Dragging

    def bind_draggable(self):
        # NOT FULLY WORKING STILL...
        self.bind("<Button-1>",
                  self.drag_mark,
                  "+")
        self.bind("<Button1-Motion>",
                  self.drag_follow,
                  "+")
        #self.bind2("<B1-Motion>", lambda e: e.widget.place(x=e.x, y=e.y), "+", "draggable")

    def unbind_draggable(self):
        pass 



# Animation methods

class AnimMixin(object):
    def __init__(self, master=None, **kwargs):
        pass

    def drag_mark(self, event):
        self._drag_mark_xy = event.x_root-event.widget.winfo_rootx(), event.y_root-event.widget.winfo_rooty()

    def drag_follow(self, event):
        xoffset,yoffset = self._drag_mark_xy
        toplevel = event.widget.winfo_toplevel()
        x,y = toplevel.winfo_pointerxy()
        x,y = (x-toplevel.winfo_rootx()-xoffset, y-toplevel.winfo_rooty()-yoffset)
        self.place(x=x, y=y)
        
    def move_to(self, endx, endy, speed="not specified", accel="not specified", deaccel="not specified", effect="not specified"):
        """
        Gradually moves a widget in a direct line towards endxy pixel coordinates.
        None of the options besides endxy are currently working.
        Note: requires that the widget uses a place manager (not pack or grid)

        - endxy: the end coordinate towards which to move the widget
        - speed: full speed pixels per ms
        - accel: 0 to 100 percentage speed buildup per ms
        - deaccel: 0 to 100 percentage speed lowering per ms
        - effect: some added effect to use on startup and slowdown (eg wobbly jello, shake)
        """
        startx,starty = (self.winfo_x(),self.winfo_y())
        xchange = endx-startx
        ychange = endy-starty
        slope = ychange/float(xchange)
        if xchange < 0:
            slope *= -1
        #movement loop
        y = starty
        def xgen(xgenstart, xgenend, step=1):
            assert isinstance(xgenstart,int)
            assert isinstance(xgenend,int)
            xgencur = xgenstart
            if xgenend < xgenstart:
                step *= -1
            while xgencur != xgenend:
                xgencur += step
                yield xgencur
        for x in xgen(1,xchange):
            x = startx + x
            y += slope
            self.place(x=x, y=int(y))
            self.update()

    def move(self, xmove, ymove, **kwargs):
        startx,starty = (self.winfo_x(),self.winfo_y())
        endx,endy = startx+xmove, starty+ymove
        self.move_to(endx, endy, **kwargs)
        
    def jitter(self, movepixels=3, frequency=0.0002, duration=0.5, pindown=True):
        """
        Jitters/shakes the widget for a certain duration.
        
        - movepixels: maximum pixels to randomly shake from base position
        - frequency: how much time in comma seconds in between each shake movement
        - duration: how long in seconds the jitter should last
        - pindown: whether to center the jittering around the widget's original starting point or to let it jitter freely and end up in a new location
        """
        mainwindow = self.winfo_toplevel()
        def func():
            if time.clock()-starttime < duration/float(1000):
                if pindown:
                    baseposx, baseposy = startposx, startposy
                else:
                    baseposx, baseposy = (self.winfo_x(), self.winfo_y())
                self.place(x=baseposx+random.randrange(-movepixels,movepixels+1),
                             y=baseposy+random.randrange(-movepixels,movepixels+1) )
                mainwindow.after(frequency, func)
            else:
                if pindown:
                    self.place(x=startposx, y=startposy)
        if pindown:
            startposx, startposy = (self.winfo_x(), self.winfo_y())
        frequency = int(frequency*1000)+1 #bc .after takes milliseconds, +1 to avoid 0 ms
        duration = int(duration*1000)+1 #bc .after takes milliseconds, +1 to avoid 0 ms
        starttime = time.clock()
        mainwindow.after(frequency, func)


# Dispatch heavy tasks mixin
class DispatchMixin(object):
    def __init__(self, master=None, **kwargs):
        pass
    
    def new_thread(self, task, args=(), kwargs={}):
        # prepare request
        resultqueue = Queue.Queue()
        task_args = (args, kwargs)
        instruct = task, task_args, resultqueue

        # begin processing in new thread
        def _compute_results_(func, func_args, resultqueue):
            "internal use only, this function is run entirely in the new worker thread"
            args, kwargs = func_args
            try:
                _results = func(*args, **kwargs)
            except Exception as errmsg:
                _results = Exception(traceback.format_exc() )
            resultqueue.put( _results )
            
        worker = threading.Thread(target=_compute_results_, args=instruct)
        worker.daemon = True
        worker._resultqueue = resultqueue
        worker._aftertasks = []
        worker.start()

        # return worker thread to user, so they can add several postprocessing steps
        return worker

    def process_thread(self, thread, func, mslag=100, msinterval=100):
        # process the results after completion
        # ...by checking the resultqueue attribute of the thread

        def _process():
            result = thread._resultqueue.get()
            func(result)
            
        self.after_thread(thread, _process, mslag=mslag, msinterval=msinterval)

    def after_thread(self, thread, task, args=(), kwargs={}, mslag=100, msinterval=100):

        instruct = (task,args,kwargs)
        thread._aftertasks.append(instruct)
        
        def _check():
            if not thread.isAlive():
                nexttask,nextargs,nextkwargs = thread._aftertasks[0]
                if nexttask == task:
                    task(*args, **kwargs)
                    thread._aftertasks.pop(0)
            else:
                self.after(msinterval, _check)
                    
        self.after(mslag, _check)


# Drag and drop mixin
class DnDMixin(object):
    def __init__(self, master=None, **kwargs):
        pass

    def bind_dnddrop(self, callback, dndtype, event='<Drop>', priority=50):
        """
        dndtype is either Files or Text.
        """
        dndobj = filednd.TkDND(self.winfo_toplevel())
        dndobj.bindtarget(self, callback, dndtype, event=event, priority=priority)

    def unbind_dnddrop(self):
        filednd.TkDND(self).cleartarget(self)

    def __str__(self):
        # Important in order for TkDnD to get widget path name
        # instead of class representation,
        # because in Python2 Tkinter widgets are oldstyle while we
        # force them into newstyle objects.
        return self.winfo_pathname(self.winfo_id())

    def __repr__(self):
        return self.__str__()



# Style mixin
##class StyleMixin(object):
##    def __init__(self, master=None, **kwargs):
##
##        # if ttk, pop kwargs to create style, then assign style
##        if "ttk." in repr(self):
##            if ".Entry" in repr(self) or ".Dropdown" in repr(self):
##                # entry and combobox dont allow font changes via styling, only via direct widget options
##                pass
##            else:
##                pass
##        
##        # else, just assign the kwargs
##        else:
##
####            # allow and bind style options when mouse is hovering
####            overoptions = dict([ (key[4:],val) for key,val in kwargs.items() if key.startswith("over")])
####            if overoptions:
####                # bind event behavior
####                def mouse_in(event):
####                    event.widget.config(overoptions)
####                def mouse_out(event):
####                    event.widget.config(overoptions)
####                self.bind("<Enter>", mouse_in, "+")
####                self.bind("<Leave>", mouse_out, "+")
##
##            pass
##
##    def configure(self, **options): 
##        # if ttk, create new unique style
##        if "ttk." in repr(self):
##            if ".Entry" in repr(self) or ".Dropdown" in repr(self):
##                # entry and combobox dont allow font changes via styling, only via direct widget options
##                if "font" in options:
##                    # change the tkvars for those options...
##                    STYLES["TEntry or TDropdown"]["configure"]["font"].set(str( options.pop("font") ))
##
##            super(StyleMixin, self).configure(**options)
##
##        # else, just assign the kwargs
##        pass
##
##    def config(self, **options):
##        # alias for configure
##        self.configure(**options)
##
##class StyleManager(object):
##    def __init__(self):
##        self.styles = dict()
##        self.styles["."] = dict()
##        self.styles["TEntry"] = dict()
##        
##    def configure(self, stylename, **kwargs):
##        pass



# Final Mixin class containing all mixins

class AllMixins(DnDMixin, DispatchMixin, AnimMixin, BindMixin):
    def __init__(self, master=None):
        BindMixin.__init__(self, master)
        AnimMixin.__init__(self, master)
        DispatchMixin.__init__(self, master)
        DnDMixin.__init__(self, master)

