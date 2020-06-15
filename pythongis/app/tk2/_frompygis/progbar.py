import Tkinter as tk

# Import style
from . import theme
style_bar_normal = {"outline": theme.color2,
                    "fill": theme.alterncolor1}
style_text_normal = {"fill": theme.font2["color"],
                    "font": theme.font2["type"]}
style_progressbar_normal = {"bg": theme.color2}

class ProgressBar(tk.Frame):
    def __init__(self, master, width, height, **kwargs):
        # Import style
        style = style_progressbar_normal.copy()
        style.update(kwargs)
        
        # Make this class a subclass of tk.Label and add to it
        tk.Frame.__init__(self, master, **style)
        
        self.queue = None
        self.progbar = None

        # Place canvas
        self.canvas = tk.Canvas(self, width=width, height=height, **style)
        self.canvas.pack(fill="both", expand=True)

    def listen(self, queue, update_ms=30, message=None):
        # Make sure it isn't already listening for something else:
        if self.queue:
            raise Exception("Wait for existing task to finish before you assign a new task to the progressbar")
        # Place empty progressbar
        width = float(self.canvas["width"])
        height = float(self.canvas["height"])
        self.progbar = self.canvas.create_rectangle(3, 3, 3, 3, **style_bar_normal)

        # Place listening text
        if message:
            center = (width / 2.0, height / 2.0)
            self.canvas.create_text(center, text=message, **style_text_normal)

        # Listen for changes to the queue
        self.queue = queue

        def keep_listening():
            ratio = self._check()
            if ratio == None:
                # failed to get progress, listen again
                self.after(update_ms, keep_listening)
            elif ratio < 1:
                print ratio
                # update progbar and keep listening
                self._draw_bar(ratio)
                self.after(update_ms, keep_listening)
            else:
                print ratio
                # finished
                self._draw_bar(ratio)
                self.after(1000, self._finish)

        keep_listening()

    def _check(self):
        try:
            return self.queue.get(block=False)
        except:
            return None

    def _draw_bar(self, ratio):
        # Calculate the new progress bar size
        width = float(self.canvas["width"]) * ratio
        height = float(self.canvas["height"])
        
        # Redraw the progressbar
        self.canvas.coords(self.progbar, (3, 3, width, height) )

    def _finish(self):
        self.queue = None
        self.progbar = None
        self.canvas.delete("all")
        
