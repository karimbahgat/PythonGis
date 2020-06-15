"""
Sub-Module of tk2: Tkinter Movement
Functions to allow easily animating and giving dynamic movement to tkinter widgets.
Note: Most of the functionality in this module requires that the widget uses a
place manager (not pack or grid)
"""

#IMPORTS
import math, random, time

#GROUP WIDGETS AND THEIR BEHAVIORS
##class Group:
##    pass
##    def Add(self):
##        pass
##    def Insert(self):
##        pass
##    def Remove(self):
##        pass
##    def Reposition(self):
##        pass

#ENTER/EXIT ANIMATIONS
def SetEnterAnim(widget, anim, trigger, **options):
    """
    Gives a widget an enter animation. Once this has been set, the widget will be hidden at startup, and will only enter if its enter trigger event occurs.

    - anim: the type of entrance animation. For now only "fly in" works. Going to add later: peek up, fade in??, flicker in, shrink/grow in, etc.
    - trigger: the GUI event that will trigger the entrance animation, given as a string the same way triggers are assigned to Tkinter trace events, eg '<Button-1>'. 
    """
    mainwindow = widget.winfo_toplevel()
    if anim == "fly in":
        if options["side"] == "left":
            def func(event):
                print ("should fly")
                MoveTo(**dict(widget=widget, endxy=(origx,origy)))
            #place outside left edge
            mainwindow.update() 
            origx,origy = (widget.winfo_x(), widget.winfo_y())
            widget.place(x=-50-widget.winfo_width(), y=origy)
            mainwindow.update()
            mainwindow.bind(trigger, func, "+")
##def SetExitAnim(widget, anim):
##    pass
##def Enter(widget):
##    pass
##def Exit(widget):
##    pass

#INTERACTION
def Draggable(widget, movepush=False, droppush=True, effect=None, dragtrigger="<Button-1>", releasetrigger="<ButtonRelease-1>"):
    """
    Makes a widget draggable
    MOSTLY WORKS, BUT CONTINUES TO DRAG EVEN AFTER RELEASETRIGGER IF SOME OTHER MOVEMENT IS STILL PROCESSING...
    Note: movepush, droppush, and effect are not currently working.
    
    - movepush: whether bumping into other widgets while being moved should push away the other widgets
    - droppush: whether releasing the drag over other widgets should push them away
    - effect: effect to use while dragging (eg MorphSize to bigger to give a lifting effect)
    - dragtrigger: tk trigger event string for when to start dragging, default is left mouseclick
    - releasetrigger: tk trigger event string for when to stop dragging, default is release of left mouseclick
    """
    widget.dragged = False
    widget.dragmaybe = False
    def mouseoverwidgetfunc(event):
        widget.dragmaybe = True
    def mouseoutofwidgetfunc(event):
        widget.dragmaybe = False
    def dragtriggerfunc(event):
        if widget.dragmaybe:
            widget.dragged = True
            widget.draganchor_xoffset = event.x_root-widget.winfo_rootx()
            widget.draganchor_yoffset = event.y_root-widget.winfo_rooty()
            widget.lift()
    def releasetriggerfunc(event):
        widget.dragged = False
        widget.draganchor_xoffset = None
        widget.draganchor_yoffset = None
    def func(event):
        if widget.dragged:
            x,y = win.winfo_pointerxy()
            x,y = (x-mainwindow.winfo_rootx()-widget.draganchor_xoffset, y-mainwindow.winfo_rooty()-widget.draganchor_yoffset)
            widget.place(x=x, y=y)
            mainwindow.update()
            #do movement
    widget.bind("<Enter>", mouseoverwidgetfunc, "+")
    widget.bind("<Leave>", mouseoutofwidgetfunc, "+")
    mainwindow = widget.winfo_toplevel()
    mainwindow.bind(dragtrigger, dragtriggerfunc, "+")
    mainwindow.bind(releasetrigger, releasetriggerfunc, "+")
    mainwindow.bind("<Motion>", func, "+")
    pass

#MOVEMENT
def MoveTo(widget, endxy, speed="not specified", accel="not specified", deaccel="not specified", effect="not specified"):
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
    def func():
        startx,starty = (widget.winfo_x(),widget.winfo_y())
        endx,endy = endxy
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
            widget.place(x=x, y=int(y))
            widget.update()
            #time.sleep(0.001)
    func()
##def MoveInDir(widget, direction, length="not specified", speed="not specified", accel="not specified", deaccel="not specified", effect="not specified"):
##    """
##    *direction - degree angle to move towards
##    *length - how many pixels to move
##    *speed - full speed pixels per ms
##    *accel - 0 to 100 percentage speed buildup per ms
##    *deaccel - 0 to 100 percentage speed lowering per ms
##    *effect - some added effect to use on startup and slowdown (eg wobbly jello, shake)
##    Note: requires that the widget uses a place manager (not pack or grid)"""
##    startx,starty = (widget.cget("x"),widget.cget("y"))
##    pass
##def MoveInCircle(widget, circlesize, stoppos):
##    pass
##def MoveCurvedPath(widget, path):
##    "should calculate bezier curve on its own"
##    pass
##def Teleport(widget, endxy, effect="not specified"):
##    pass
##def GravityFall(widget):
##    pass

#EFFECTS
def MorphSize(widget, sizechange, duration=0.5):
    """
    Gradually changes the size of the widget
    WORK IN PROGRESS, INACCURATE CUS SIZE DEPENDENT ON TIME SPEED
    
    - sizechange: xtimes change in size (eg 2x twice as large), negative number of shrink, 1 if stay same, and 0 is not possible
    - duration: time in seconds it should take to morph to new size, currently not working properly
    """
    mainwindow = widget.winfo_toplevel()
    def func(newwidth,newheight):
        if time.clock()-starttime < duration/float(1000):
            newwidth,newheight = (newwidth+widthincr, newheight+heightincr)
            widget.place(width=int(round(newwidth)), height=int(round(newheight)))
            widget.update()
            mainwindow.after(0, func, newwidth, newheight)
    duration = int(duration*1000)+1 #bc .after takes milliseconds, +1 to avoid 0 ms
    width,height = (widget.winfo_width(), widget.winfo_height())
    if sizechange < 0:
        sizechange = 1/float(sizechange)
    finalwidth,finalheight = (width*sizechange,height*sizechange)
    widthincr = (finalwidth/float(duration))
    heightincr = (finalheight/float(duration))
    starttime = time.clock()
    func(width,height)
def Jitter(widget, movepixels=3, frequency=0.0002, duration=0.5, pindown=True):
    """
    Jitters/shakes the widget for a certain duration.
    
    - movepixels: maximum pixels to randomly shake from base position
    - frequency: how much time in comma seconds in between each shake movement
    - duration: how long in seconds the jitter should last
    - pindown: whether to center the jittering around the widget's original starting point or to let it jitter freely and end up in a new location
    """
    mainwindow = widget.winfo_toplevel()
    def func():
        if time.clock()-starttime < duration/float(1000):
            if pindown:
                baseposx, baseposy = startposx, startposy
            else:
                baseposx, baseposy = (widget.winfo_x(), widget.winfo_y())
            widget.place(x=baseposx+random.randrange(-movepixels,movepixels+1),
                         y=baseposy+random.randrange(-movepixels,movepixels+1) )
            mainwindow.after(frequency, func)
        else:
            if pindown:
                widget.place(x=startposx, y=startposy)
    if pindown:
        startposx, startposy = (widget.winfo_x(), widget.winfo_y())
    frequency = int(frequency*1000)+1 #bc .after takes milliseconds, +1 to avoid 0 ms
    duration = int(duration*1000)+1 #bc .after takes milliseconds, +1 to avoid 0 ms
    starttime = time.clock()
    mainwindow.after(frequency, func)
##def Wobble(widget):
##    pass

#TESTING
if __name__ == "__main__":
    #PYTHON VERSION CHECKING
    import sys
    PYTHON3 = int(sys.version[0]) == 3
    if PYTHON3:
        xrange = range
        import tkinter as tk
    else:
        import Tkinter as tk
    win = tk.Tk()
    frame = tk.Frame(width=500, height=500, bg="yellow")
    frame.pack()
    
    #create widgets and their commands
    movebut = tk.Button(frame, text="move to")
    movebut["command"] = lambda: MoveTo(**dict(widget=movebut, endxy=(200,100)))
    movebut.place(x=20, y=20)
    jitterbut = tk.Button(frame, text="jitter")
    jitterbut["command"] = lambda: Jitter(**dict(widget=jitterbut))
    jitterbut.place(x=20, y=50)
    growbut = tk.Button(frame, text="grow/shrink")
    def makegrow(event):
        MorphSize(**dict(widget=growbut, sizechange=2))
    def makeshrink(event):
        MorphSize(**dict(widget=growbut, sizechange=-2))
    growbut.bind("<Enter>", makegrow, "+")
    growbut.bind("<Leave>", makeshrink, "+")
    growbut.place(x=20, y=80)
    enterbut = tk.Button(frame, text="enterbut")
    enterbut.place(x=200,y=300)
    enterinstruct = tk.Label(frame, text="there should be one more widget here, press enter to make it appear", bg="yellow", relief="flat", wraplength=160)
    enterinstruct.place(x=200,y=300, height=188, width=188)
    enterinstruct.lower()
    SetEnterAnim(enterbut, "fly in", "<Return>", side="left")
    
    #make widgets draggable
    Draggable(movebut)
    Draggable(jitterbut)
    Draggable(growbut)
    win.mainloop()
