
from .map import MapView

def view_data(data, width=None, height=None, bbox=None, flipy=True, **styleoptions):
    mapp = data.render(width, height, bbox, flipy, **styleoptions)
    
    import tk2
    
    win = tk2.Tk()

    mapview = MapView(win, mapp)
    mapview.pack(fill="both", expand=1)
    
    return win
