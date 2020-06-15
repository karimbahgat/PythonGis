"""
Sub-Module of Tk2: Tkinter Placer
Provides functions to add gradient color backgrounds to widgets for
a smoother and more dynamic Tkinter GUI look. 
"""

import sys, random

#PYTHON VERSION CHECKING
import sys
PYTHON3 = int(sys.version[0]) == 3
if PYTHON3:
    xrange = range
    import tkinter as tk
    def izip(*inlists):
        return zip(*inlists)
    def listzip(*inlists):
        return list(zip(*inlists))
else:
    import Tkinter as tk
    import itertools
    def izip(*inlists):
        return itertools.izip(*inlists)
    def listzip(*inlists):
        return zip(*inlists)

#INTERNAL USE ONLY
def _ResizeList(rows, newlength, stretchmethod="not specified", gapvalue=None):
    """
    Resizes (up or down) and returns a new list of a given size, based on an input list.
    - rows: the input list, which can contain any type of value or item (except if using the interpolate stretchmethod which requires floats or ints only)
    - newlength: the new length of the output list (if this is the same as the input list then the original list will be returned immediately)
    - stretchmethod: if the list is being stretched, this decides how to do it. Valid values are:
      - 'interpolate'
        - linearly interpolate between the known values (automatically chosen if list contains ints or floats)
      - 'duplicate'
        - duplicate each value so they occupy a proportional size of the new list (automatically chosen if the list contains non-numbers)
      - 'spread'
        - drags the original values apart and leaves gaps as defined by the gapvalue option
    - gapvalue: a value that will be used as gaps to fill in between the original values when using the 'spread' stretchmethod
    """
    #return input as is if no difference in length
    if newlength == len(rows):
        return rows
    #set auto stretchmode
    if stretchmethod == "not specified":
        if isinstance(rows[0], (int,float)):
            stretchmethod = "interpolate"
        else:
            stretchmethod = "duplicate"
    #reduce newlength 
    newlength -= 1
    #assign first value
    outlist = [rows[0]]
    writinggapsflag = False
    if rows[1] == gapvalue:
        writinggapsflag = True
    relspreadindexgen = (index/float(len(rows)-1) for index in xrange(1,len(rows))) #warning a little hacky by skipping first index cus is assigned auto
    relspreadindex = next(relspreadindexgen)
    spreadflag = False
    gapcount = 0
    for outlistindex in xrange(1, newlength):
        #relative positions
        rel = outlistindex/float(newlength)
        relindex = (len(rows)-1) * rel
        basenr,decimals = str(relindex).split(".")
        relbwindex = float("0."+decimals)
        #determine equivalent value
        if stretchmethod=="interpolate":
            #test for gap
            maybecurrelval = rows[int(relindex)]
            maybenextrelval = rows[int(relindex)+1]
            if maybecurrelval == gapvalue:
                #found gapvalue, so skipping and waiting for valid value to interpolate and add to outlist
                gapcount += 1
                continue
            #test whether to interpolate for previous gaps
            if gapcount > 0:
                #found a valid value after skipping gapvalues so this is where it interpolates all of them from last valid value to this one
                startvalue = outlist[-1]
                endindex = int(relindex)
                endvalue = rows[endindex]
                gapstointerpolate = gapcount 
                allinterpolatedgaps = _ResizeList([startvalue,endvalue],gapstointerpolate+3)
                outlist.extend(allinterpolatedgaps[1:-1])
                gapcount = 0
                writinggapsflag = False
            #interpolate value
            currelval = rows[int(relindex)]
            lookahead = 1
            nextrelval = rows[int(relindex)+lookahead]
            if nextrelval == gapvalue:
                if writinggapsflag:
                    continue
                relbwval = currelval
                writinggapsflag = True
            else:
                relbwval = currelval + (nextrelval - currelval) * relbwindex #basenr pluss interindex percent interpolation of diff to next item
        elif stretchmethod=="duplicate":
            relbwval = rows[int(round(relindex))] #no interpolation possible, so just copy each time
        elif stretchmethod=="spread":
            if rel >= relspreadindex:
                spreadindex = int(len(rows)*relspreadindex)
                relbwval = rows[spreadindex] #spread values further apart so as to leave gaps in between
                relspreadindex = next(relspreadindexgen)
            else:
                relbwval = gapvalue
        #assign each value
        outlist.append(relbwval)
    #assign last value
    if gapcount > 0:
        #this last value also has to interpolate for previous gaps       
        startvalue = outlist[-1]
        endvalue = rows[-1]
        gapstointerpolate = gapcount 
        allinterpolatedgaps = _ResizeList([startvalue,endvalue],gapstointerpolate+3)
        outlist.extend(allinterpolatedgaps[1:-1])
        outlist.append(rows[-1])
        gapcount = 0
        writinggapsflag = False
    else:
        outlist.append(rows[-1])
    return outlist


#USER FUNCTIONS
def AddGradientBackground(widget, colorstops, direction="vertical", width="option", height="option"):
    """
    Adds a gradient background to a widget.
    Note: The gradient works best on widgets whose width/height have been set manually as an option, and is not dynamically determined by a geometry manager.
    In particular, the gradient will not be updated to the new dimensions if your widget changes its size during runtime.
    If you are using a geometry manager to determine the size of the widget you can set the gradient width/height with the "auto" option.
    But be careful with doing this prior to the application has been created, since the actual sizes aren't fully negotiated until the application is fully created,
    and because to retrieve them this method has to update and thus display the window, which will look odd if it is still in its startup phase.

    - widget: the widget to give the gradient background. Note: The widget must support displaying images, so eg passing a root window or a Frame widget will result in an error.
    - colorstops: a list of RGB color tuples, each representing the colors to cycle through in the gradient. Must have at least two colors.
    - direction: a string indicating the direction of the gradient. "horizontal" to make it go to the right, or "vertical" to make it go upwards (default).
    - width: a string indicating how to determine the width of the gradient image. Set to "option" to read the width from the widget's width attribute (default) or "auto" to read the actual width as has been set by its geometry manager. Can also be specified directly as an integer.
    - height: a string indicating how to determine the height of the gradient image. Set to "option" to read the height from the widget's height attribute (default) or "auto" to read the actual height as has been set by its geometry manager. Can also be specified directly as an integer.
    
    """
    #get widget dimensions
    if width == "auto":
        widget.winfo_toplevel().update_idletasks()
        width = widget.winfo_width()
    elif width == "option":
        width = widget["width"]
    if height == "auto":
        widget.winfo_toplevel().update_idletasks()
        height = widget.winfo_height()
    elif height == "option":
        height = widget["height"]
    #generate gradient colors
    if direction == "horizontal": gradlen = width
    elif direction == "vertical": gradlen = height
    crosssection = izip(*colorstops)
    grad_crosssection = [ _ResizeList(spectrum,gradlen,stretchmethod="interpolate") for spectrum in crosssection ]
    gradient = izip(*grad_crosssection)
    #create tk image based on dims
    gradimg = tk.PhotoImage(width=width, height=height)
    #fill image with gradient lines
    if direction == "horizontal":
        gradient = list(gradient)
        imgstring = " ".join(["{"+" ".join(["#%02x%02x%02x" %tuple(rgb) for rgb in gradient])+"}" for _ in xrange(width)])
    elif direction == "vertical":
        imgstring = " ".join(["{"+" ".join(["#%02x%02x%02x" %tuple(rgb) for _ in xrange(width)])+"}" for rgb in gradient])
    gradimg.put(imgstring)
    #assign gradient image as background image to widget
    widget.gradient_bg = gradimg
    widget["image"] = widget.gradient_bg
    widget["compound"] = "center"
    return widget

if __name__ == "__main__":
    #just a little test case
    win = tk.Tk()
    frame = tk.Label(win, width=500, height=500)
    frame.place(relx=0.5,rely=0.5,anchor="center")
    lbl = tk.Label(win, text="what a nice sunset", width=88, height=40)
    lbl.place(relx=0.5,rely=0.5, anchor="center")
    AddGradientBackground(frame, [(0,0,222),(0,222,0),(222,0,0)], width="option", height="option")
    AddGradientBackground(lbl, [(0,0,222),(222,0,0)], direction="horizontal", width="option", height="option")
    win.mainloop()

