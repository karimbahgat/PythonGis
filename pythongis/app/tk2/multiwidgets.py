"""
Add multichoice widget,
multientry widget,
and maybe possibility to link these hierarchically (one depends on answers of previous)?
"""

# Imports

import sys
if sys.version.startswith("2"):
    import Tkinter as tk
else: import tkinter as tk
import ttk
from . import mixins as mx
from . import basics as bs
from . import scrollwidgets as sw



# Classes

class Multiselect(mx.AllMixins, tk.Frame):
    def __init__(self, master, choices, **kwargs):
        master = mx.get_master(master)
        tk.Frame.__init__(self, master, **kwargs)

        # add the listbox where all selections will be added
        inputwidget = self.inputwidget = sw.Listbox(self)
        inputwidget.pack(fill="x", expand=1, side="right", anchor="ne", padx=3)
        
        # add a listbox of choices to choose from
        def addtolist():
            for selectindex in fromlist.curselection():
                selectvalue = fromlist.get(selectindex)
                inputwidget.insert(tk.END, selectvalue)
            for selectindex in reversed(fromlist.curselection()):
                fromlist.delete(selectindex)
        def dropfromlist():
            for selectindex in inputwidget.curselection():
                selectvalue = inputwidget.get(selectindex)
                fromlist.insert(tk.END, selectvalue)
            for selectindex in reversed(inputwidget.curselection()):
                inputwidget.delete(selectindex)
                
        # define buttons to send back and forth bw choices and input
        buttonarea = tk.Frame(self)
        buttonarea.pack(side="right", anchor="n")
        addbutton = bs.Button(buttonarea, command=addtolist,
                               text="+")
        addbutton.pack(anchor="ne", padx=3, pady=3)
        dropbutton = bs.Button(buttonarea, command=dropfromlist,
                               text="-")
        dropbutton.pack(anchor="ne", padx=3, pady=3)
        
        # create and populate the choices listbox
        fromlist = self.fromlist = sw.Listbox(self)
        for ch in choices:
            fromlist.insert(tk.END, ch)
        fromlist.pack(fill="x", expand=1, side="left", anchor="ne", padx=3)

    def set_choices(self, choices):
        self.fromlist.delete(0, tk.END)
        for ch in choices:
            self.fromlist.insert(tk.END, ch)

    def get(self):
        return self.inputwidget.get()


class Multientry(mx.AllMixins, tk.Frame):
    def __init__(self, master, **kwargs):
        master = mx.get_master(master)
        tk.Frame.__init__(self, master, **kwargs)

        # add the listbox where all selections will be added
        inputwidget = sw.Listbox(self)
        inputwidget.pack(fill="x", expand=1, side="right", anchor="ne", padx=3)
        
        # add a freeform entry field and button to add to the listbox
        def addtolist():
            entryvalue = addentry.get()
            inputwidget.insert(tk.END, entryvalue)
            addentry.delete(0, tk.END)
        def dropfromlist():
            for selectindex in reversed(inputwidget.curselection()):
                inputwidget.delete(selectindex)

        # define buttons to send back and forth bw choices and input
        buttonarea = tk.Frame(self)
        buttonarea.pack(side="right", anchor="n")
        addbutton = bs.Button(buttonarea, command=addtolist,
                               text="+")
        addbutton.pack(anchor="ne", padx=3, pady=0)
        dropbutton = bs.Button(buttonarea, command=dropfromlist,
                               text="-")
        dropbutton.pack(anchor="ne", padx=3, pady=3)
        
        # place the freeform text entry widget
        addentry = bs.Entry(self)
        addentry.pack(fill="x", expand=1, side="left", anchor="ne", padx=3)
        

