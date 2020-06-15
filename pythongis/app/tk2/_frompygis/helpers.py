
import itertools

# GUI Helpers

def trackloop(iterable, queue, updateincr=1):
    # make updateincr to fraction of one 
    updateincr = updateincr / 100.0

    # setup
    total = float(len(iterable))
    nextthresh = updateincr

    # begin
    for index, item in enumerate(iterable):
        prog = index
        ratio = prog / total
        if ratio >= nextthresh:
            nextthresh += updateincr
            #if not queue.empty():
            #    queue.get()
            queue.put(ratio)

        # yield next element from iterable
        yield item

    # check for finish
    queue.put(1.0)



# example testing
if __name__ == "__main__":
    from Queue import Queue
    q = Queue()
    iter = range(1000000)
    for each in progress(iter, 20, q):
        try: print q.get(block=False)
        except: pass
    print q.get()
    print ("done")



              

            
