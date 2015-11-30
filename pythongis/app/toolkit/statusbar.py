
# Import GUI
import Tkinter as tk

# Import style
from . import theme
style_statusbar_normal = {"height": 25,
                          "bg": theme.color3}
style_status_normal = {"fg": theme.font2["color"],
                       "font": theme.font2["type"],
                       "bg": theme.color3}
style_taskstatus_normal = style_status_normal.copy()
style_taskstatus_working = {"fg": theme.font1["color"],
                            "font": theme.font1["type"],
                            "bg": theme.strongcolor2}

# Status Bars

class StatusBar(tk.Frame):
    def __init__(self, master, **kwargs):
        """
        A container bar that contains one or more status widgets
        """
        # get theme style
        style = style_statusbar_normal.copy()
        style.update(kwargs)

        # Make this class a subclass of tk.Frame and add to it
        tk.Frame.__init__(self, master, **style)

        # Insert status items
        self.task = TaskStatus(self)
        self.task.place(relx=0.0, rely=0.5, anchor="w") 
        self.projection = ProjectionStatus(self)
        self.projection.place(relx=0.20, rely=0.5, anchor="w") 
        self.zoom = ZoomStatus(self)
        self.zoom.place(relx=0.40, rely=0.5, anchor="w") 
        self.mouse = MouseStatus(self)
        self.mouse.place(relx=0.70, rely=0.5, anchor="w") 

class Status(tk.Label):
    def __init__(self, master, **kwargs):
        """
        The base class used for all status widgets
        """
        # get theme style
        style = style_status_normal.copy()
        style.update(kwargs)
        
        # Make this class a subclass of tk.Label and add to it
        tk.Label.__init__(self, master, **style)
        self.prefix = ""

    def set_text(self, text):
        self["text"] = self.prefix + text

    def clear_text(self):
        self["text"] = self.prefix

class TaskStatus(Status):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Label and add to it
        default = {"width":30, "anchor":"w"}
        default.update(kwargs)
        Status.__init__(self, master, **default)

        # Set startup status
        self.set_text("Ready")

    def start(self, taskname):
        self.config(**style_taskstatus_working)
        self.set_text(taskname)

    def stop(self):
        self.set_text("Finished!")
        self.config(**style_taskstatus_normal)
        def reset_text():
            self.set_text("Ready")
        self.after(1000, reset_text)

class ProjectionStatus(Status):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Label and add to it
        self.prefix = "Map Projection: "
        default = {"text":self.prefix, "width":30, "anchor":"w"}
        default.update(kwargs)
        Status.__init__(self, master, **default)

class ZoomStatus(Status):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Label and add to it
        self.prefix = "Horizontal Scale: "
        default = {"text":self.prefix, "width":30, "anchor":"w"}
        default.update(kwargs)
        Status.__init__(self, master, **default)

class MouseStatus(Status):
    def __init__(self, master, **kwargs):
        # Make this class a subclass of tk.Label and add to it
        self.prefix = "Mouse coordinates: "
        default = {"text":self.prefix, "width":50, "anchor":"w"}
        default.update(kwargs)
        Status.__init__(self, master, **default)




        
