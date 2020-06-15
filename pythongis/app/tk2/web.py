"""
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

class UserLogin(mx.AllMixins, tk.Frame):
    def __init__(self, master, callback, **kwargs):
        master = mx.get_master(master)
        tk.Frame.__init__(self, master, **kwargs)
        mx.AllMixins.__init__(self, master)

        # center
        center = bs.Label(self)
        center.pack()

        # username entry
        uname = bs.Entry(center, label="Username")
        uname.pack(fill="x")

        # password entry
        pword = bs.Entry(center, label="Password", show="*")
        pword.pack(fill="x")

        # submit
        def trylogin(*pointless):
            u = uname.get()
            p = pword.get()
            success = callback(u, p)
            if success:
                #self.destroy()
                pass
            else:
                failmsg = bs.Label(center, text="*Login failed", foreground="red")
                failmsg.pack()
        submit = bs.Button(center, text="Login", command=trylogin)
        uname.interior.bind("<Return>", trylogin)
        pword.interior.bind("<Return>", trylogin)
        submit.pack()



