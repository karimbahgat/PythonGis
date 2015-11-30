
import threading
import Queue
import traceback

def request_results(func, args=(), kwargs={}):
    # prepare request
    results = Queue.Queue()
    func_args = (args, kwargs)
    instruct = func, func_args, results

    # ask the thread
    worker = threading.Thread(target=_compute_results_, args=instruct)
    worker.daemon = True
    worker.start()

    # return the empty results, it is up to the GUI to wait for it
    return results

def after_completion(window, queue, func):
    
    def check():
        try:
            result = queue.get(block=False)
        except:
            window.after(1000, check)
        else:
            func(result)
                
    window.after(100, check)

def _compute_results_(func, func_args, results):
    """
    This is where the actual work is done,
    and is run entirely in the new worker thread.
    """
    args, kwargs = func_args
    try: _results = func(*args, **kwargs)
    except Exception as errmsg:
        _results = Exception(traceback.format_exc() )
    results.put( _results )





