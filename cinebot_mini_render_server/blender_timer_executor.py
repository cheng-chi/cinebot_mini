import bpy
from concurrent.futures import Executor, Future, ThreadPoolExecutor
import queue
import weakref


class _WorkItem(object):
    def __init__(self, future, fn, args, kwargs):
        self.future = future
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        if not self.future.set_running_or_notify_cancel():
            return

        try:
            result = self.fn(*self.args, **self.kwargs)
        except BaseException as e:
            self.future.set_exception(e)
        else:
            self.future.set_result(result)


class BlenderTimerExecutor(Executor):
    def __init__(self, delay=0.001):
        self._work_queue = queue.Queue()
        self._shutdown = False
        self._delay = delay
        self._registered = False
    
    def submit(self, fn, *args, **kwargs):
        f = Future()
        w = _WorkItem(f, fn, args, kwargs)

        self._work_queue.put(w)
        self._start_worker()
        return f
    
    def _start_worker(self):
        def work_once():
            executor_ref = weakref.ref(self)
            # print("Executor!", executor_ref()._delay)
            try:
                while True:
                    work_item = executor_ref()._work_queue.get(False)
                    if work_item is not None:
                        work_item.run()
                        del work_item
                    else:
                        return None
            except queue.Empty:
                # print("Nothing to work on! Sleep")
                temp = executor_ref()._delay
            except Exception as e:
                print("Exception in executor!", e)

            return executor_ref()._delay
        
        if not self._registered:
            bpy.app.timers.register(work_once)
            self._registered = True


EXECUTOR = BlenderTimerExecutor()
