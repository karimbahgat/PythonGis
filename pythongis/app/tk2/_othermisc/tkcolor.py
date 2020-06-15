"""
Sub-Module of Tk2: Tkinter Color
Provides functions to easily create and modify colors to be used for coloring
Tkinter GUI widgets, allowing greater flexibility than the builtin Tkinter
color names. Builds on functionality from the Valentin Lab's Colour module
which it uses behind the scenes. See: https://pypi.python.org/pypi/colour/0.0.5
"""

import sys, random, colour

#PYTHON VERSION CHECKING
import sys
PYTHON3 = int(sys.version[0]) == 3
if PYTHON3:
    xrange = range
    import tkinter as tk
    import tkinter.colorchooser as tkColorChooser
    def izip(*inlists):
        return zip(*inlists)
    def listzip(*inlists):
        return list(zip(*inlists))
else:
    import Tkinter as tk
    import tkColorChooser
    import itertools
    def izip(*inlists):
        return itertools.izip(*inlists)
    def listzip(*inlists):
        return zip(*inlists)


#MAIN
    
COLORSTYLES = dict([("strong", dict( [("intensity",1), ("brightness",0.5)]) ),
                ("dark", dict( [("intensity",0.8), ("brightness",0.2)]) ),
                ("matte", dict( [("intensity",0.4), ("brightness",0.2)]) ),
                ("bright", dict( [("intensity",0.8), ("brightness",0.7)] ) ),
                ("weak", dict( [("intensity",0.3), ("brightness",0.5)] ) ),
                ("pastelle", dict( [("intensity",0.5), ("brightness",0.6)] ) )
                ])

def Color(basecolor, intensity="not specified", brightness="not specified", style=None):
    """
    Returns a hex color string of the color options specified. Meant to allow
    greater flexibility and convenience than the builtin Tkinter color names.
    Is built on top of the Valentin Lab's Colour module which it uses behind
    the scenes. See: https://pypi.python.org/pypi/colour/0.0.5

    **Arguments:**

    - basecolor: the human-like name of a color. Always required, but can also be set to 'random'. 
    - *intensity: how strong the color should be. Must be a float between 0 and 1, or set to 'random' (by default uses the 'strong' style values, see 'style' below). 
    - *brightness: how light or dark the color should be. Must be a float between 0 and 1 , or set to 'random' (by default uses the 'strong' style values, see 'style' below).
    - *style: a named style that overrides the brightness and intensity options (optional). See list of valid style names below.

    Valid style names are:

    - 'strong'
    - 'dark'
    - 'matte'
    - 'bright'
    - 'pastelle'
    """
    #first check on intens/bright
    if style and basecolor not in ("black","white","gray"):
        #style overrides manual intensity and brightness options
        intensity = COLORSTYLES[style]["intensity"]
        brightness = COLORSTYLES[style]["brightness"]
    else:
        #special black,white,gray mode, bc random intens/bright starts creating colors, so have to be ignored
        if basecolor in ("black","white","gray"):
            if brightness == "random":
                brightness = random.randrange(20,80)/100.0
        #or normal
        else:
            if intensity == "random":
                intensity = random.randrange(20,80)/100.0
            elif intensity == "not specified":
                intensity = 0.7
            if brightness == "random":
                brightness = random.randrange(20,80)/100.0
            elif brightness == "not specified":
                brightness = 0.5
    #then assign colors
    if basecolor in ("black","white","gray"):
        #graymode
        if brightness == "not specified":
            return colour.Color(color=basecolor).hex
        else:
            #only listen to gray brightness if was specified by user or randomized
            return colour.Color(color=basecolor, luminance=brightness).hex
    elif basecolor == "random":
        #random colormode
        basecolor = random.randrange(300)
        return colour.Color(pick_for=basecolor, saturation=intensity, luminance=brightness).hex
    else:
        #custom made color
        return colour.Color(color=basecolor, saturation=intensity, luminance=brightness).hex

def AskColor(text="unknown graphics"):
    """
    Pops up a temporary tk window asking user to visually choose a color.
    Returns the chosen color as a hex string. Also prints it as text in case
    the user wants to remember which color was picked and hardcode it in the script.

    - *text: an optional string to identify what purpose the color was chosen for when printing the result as text.
    """
    def askcolor():
        tempwindow = tk.Tk()
        tempwindow.state("withdrawn")
        rgb,hexcolor = tkColorChooser.askcolor(parent=tempwindow, title="choose color for "+text) ;
        tempwindow.destroy()
        print("you picked the following color for "+str(text)+": "+str(hexcolor))
        return hexcolor
    hexcolor = askcolor()
    return colour.Color(hexcolor).hex

if __name__ == "__main__":
    print (Color(basecolor="blue", style="pastelle") )
