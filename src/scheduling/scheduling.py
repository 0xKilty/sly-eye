import logging
import os
from concurrent.futures import ProcessPoolExecutor
import threading

logger = logging.getLogger("sly-eye")

class BoundedProcessPool:
    def __init__(self, max_workers=None):
        # Default: number of CPU cores, fallback to 4
        self._cores = os.cpu_count() or 4
        self._max_workers = max_workers or min(3, self._cores)

        # Use processes, not threads
        self._executor = ProcessPoolExecutor(max_workers=self._max_workers)

        # Semaphore to limit how many futures are "in flight"
        self._semaphore = threading.Semaphore(self._max_workers)

    def submit(self, fn, *args, **kwargs):
        # Must be a top-level function (picklable!)
        self._semaphore.acquire()
        future = self._executor.submit(fn, *args, **kwargs)

        # Release the slot once task is done
        future.add_done_callback(lambda _: self._semaphore.release())
        return future

    def shutdown(self, wait=True):
        self._executor.shutdown(wait)
