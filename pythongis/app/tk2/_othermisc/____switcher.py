
from . import scrollwidgets as sw
from . import mixins as mx

class Switcher(sw.Frame):
    def __init__(self, master, **kwargs):
        sw.Frame.__init__(self, master, **kwargs)
        self.frames = []

    def add(self, frame, name=None):
        # give each added frame a method for switching to another frame
        frame.switch = self.switch
        frame.name = name
        frame.place(relwidth=1, relheight=1)
        self.frames.append(frame)

    def switch(self, new):
        if isinstance(new, int):
            new = self.frames[new]
        else:
            new = next(f for f in self.frames if f.name and new == f.name)
        new.lift()
        return new

    
