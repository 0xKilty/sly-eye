import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = logging.getLogger("sly-eye")

class Scheduler:
    def __init__(self):
        self.cores = os.cpu_count() or 4
        self.max_workers = min(32, self.cores * 2)

def bulk_scan(function, images, max_workers=4):
    results = {}
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(function, img): img for img in images}
        for future in as_completed(futures):
            img = futures[future]
            try:
                _, scan_results = future.result()
                results[img] = scan_results
                logger.info(f"Finished scanning {img} ({len(scan_results)} findings)")
            except Exception as e:
                logger.error(f"Error scanning {img}: {e}")
                results[img] = []
    return results


'''

scheduler = Scheduler()

scheduler.dispatch(run_trufflehog, images)

'''
