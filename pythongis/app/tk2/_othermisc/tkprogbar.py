import Tkinter as tk
from Queue import Queue


class ProgressBar(tk.Frame):
    def __init__(self, master, queue, maxvalue, **kwargs):
        tk.Frame.__init__(self, master, **kwargs)

        # create the label that will show the progress
        progbar = tk.Label(self, bg=kwargs.get("fg", "green"), relief="ridge")
        progbar.queue = queue
        progbar.place(relx=0, rely=0, relwidth=progbar.queue.get(), relheight=1)

        # begin looping to check for changes
        def keepchecking():
            progress = progbar.queue.get() / maxvalue
            progbar.config( relwidth=progress )
            progbar.update()
            if progress < maxvalue:
                progbar.after(10, keepchecking)
        progbar.after(10, keepchecking)


w = tk.Tk()
q = Queue()
q.put(0)
p = ProgressBar(w, q, 100)
p.pack(width=300, height=100)

def incr():
    q.put(q.get()+1)
    q.after(10, incr)
q.after(10, incr)
w.mainloop()




