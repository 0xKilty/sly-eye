import logging
import os
from concurrent.futures import ThreadPoolExecutor
import threading

logger = logging.getLogger("sly-eye")

class BoundedExecutor:
    def __init__(self):
        self._cores = os.cpu_count() or 4
        self._max_workers = 3

        self._executor = ThreadPoolExecutor(max_workers=self._max_workers)
        self._queue = threading.Semaphore(self._max_workers)

    def submit(self, fn, *args, **kwargs):
        self._queue.acquire()
        future = self._executor.submit(fn, *args, **kwargs)
        future.add_done_callback(lambda f: self._queue.release())
        return future

    def shutdown(self, wait=True):
        self._executor.shutdown(wait)

