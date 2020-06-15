

import sys
if sys.version.startswith("2"):
    import Tkinter as tk
    from Tkinter import BooleanVar, StringVar, IntVar, DoubleVar
else:
    import tkinter as tk
    from tkinter import BooleanVar, StringVar, IntVar, DoubleVar


##class BooleanVar(tk.BooleanVar):
##    def __init__(self, master=None, **kwargs):
##        tk.BooleanVar.__init__(self, master, **kwargs)
##
##class StringVar(tk.StringVar):
##    def __init__(self, master=None, **kwargs):
##        tk.StringVar.__init__(self, master, **kwargs)
##
##class IntVar(tk.IntVar):
##    def __init__(self, master=None, **kwargs):
##        tk.IntVar.__init__(self, master, **kwargs)
##        
##    def __add__(self, other):
##        return self.get() + other
##
##    def __radd__(self, other):
##        return other + self.get()
##
##    def __sub__(self, other):
##        return self.get() - other
##
##    def __rsub__(self, other):
##        return other - self.get()
##
##class DoubleVar(IntVar, tk.DoubleVar):
##    def __init__(self, master=None, **kwargs):
##        tk.DoubleVar.__init__(self, master, **kwargs)
