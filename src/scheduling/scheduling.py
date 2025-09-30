import logging
import os
from concurrent.futures import ProcessPoolExecutor
import threading

logger = logging.getLogger("sly-eye")

class BoundedProcessPool:
    def __init__(self, max_workers=None):
        self._cores = os.cpu_count() or 4
        self._max_workers = max_workers or min(3, self._cores)
        
        self._executor = ProcessPoolExecutor(max_workers=self._max_workers)
        self._semaphore = threading.Semaphore(self._max_workers)

    def submit(self, fn, *args, **kwargs):
        self._semaphore.acquire()
        future = self._executor.submit(fn, *args, **kwargs)
        future.add_done_callback(lambda _: self._semaphore.release())
        return future

    def shutdown(self, wait=True):
        self._executor.shutdown(wait)
