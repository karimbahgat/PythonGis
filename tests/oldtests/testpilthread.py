
import PIL, PIL.Image
from time import time
import threading

path = r"C:\Users\kimok\Desktop\redd barna\Maps\case validation, u18 percdiff NGA.png"
img = PIL.Image.open(path)

### normal python
##t=time()
##for _ in range(30):
##    img.resize((100,100), PIL.Image.ANTIALIAS)
##print time()-t
##
### thread directly to C func (fast)
##t=time()
##threads = []
##for _ in range(30):
##    th = threading.Thread(target=img.resize, args=[(100,100), PIL.Image.ANTIALIAS])
##    th.start()
##    threads.append(th)
##print 'started',time()-t
##for th in threads:
##    th.join()
##print 'finished',time()-t
##
### thread via pure python func (slower)
##def resize():
##    img.resize((1000,1000), PIL.Image.ANTIALIAS)
##
##t=time()
##threads = []
##for _ in range(30):
##    th = threading.Thread(target=resize)
##    th.start()
##    threads.append(th)
##print 'started',time()-t
##for th in threads:
##    th.join()
##print 'finished',time()-t


########
# resize and paste into new
if 1:
    img.load() # must call load first, otherwise multiple calls will break it

    # normal python
    out = PIL.Image.new('RGB', (1000,1000), 255)

    t=time()
    for x in range(0,1000,200):
        for y in range(0,1000,200):
            res = img.resize((200,200), PIL.Image.ANTIALIAS)
            out.paste(res, (x,y))
    print time()-t

    # thread via pure python func (slower)
    out = PIL.Image.new('RGB', (1000,1000), 255)

    def resize(x,y):
        res = img.resize((200,200), PIL.Image.ANTIALIAS)
        out.paste(res, (x,y))

    t=time()
    threads = []
    for x in range(0,1000,200):
        for y in range(0,1000,200):
            th = threading.Thread(target=resize, args=(x,y))
            th.start()
            threads.append(th)
    print 'started',time()-t
    for th in threads:
        th.join()
    print 'finished',time()-t
    out.show()



#########
# drawing
if 0:
    img.load() # must call load first, otherwise multiple calls will break it

    # normal python
    import PIL.ImageDraw
    out = PIL.Image.new('RGB', (1000,1000), 255)
    drawer = PIL.ImageDraw.Draw(out)
    coords = [(x,y) for x in range(100,900,1) for y in range(100,900,10)]

    t=time()
    for x in range(0,1000,200):
        for y in range(0,1000,200):
            drawer.polygon(coords, 'red', 'black')
    print time()-t

    # thread (doesnt work for drawing...)
    import PIL.ImageDraw
    out = PIL.Image.new('RGB', (1000,1000), 255)
    drawer = PIL.ImageDraw.Draw(out)
    coords = [(x,y) for x in range(100,900,1) for y in range(100,900,10)]

    def rend():
        drawer.polygon(coords, 'red', 'black')

    t=time()
    threads = []
    for x in range(0,1000,200):
        for y in range(0,1000,200):
            th = threading.Thread(target=drawer.polygon, args=(coords, 'red', 'black'))
            #th = threading.Thread(target=rend)
            th.start()
            threads.append(th)
    print 'started',time()-t
    for th in threads:
        th.join()
    print 'finished',time()-t

    print time()-t






