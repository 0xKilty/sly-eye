import logging
import coloredlogs
import argparse
from elasticsearch import helpers

from src.sourcing.dockerhub import dockerhub_source
from src.scanning.trufflehog import TruffleHog
from src.storing.elastic import start_elastic
from src.searching.kibana import start_kibana
from src.scheduling.scheduling import BoundedProcessPool

def display_logo():
    logo = r"""
            ..,,;;;;;;,,,,
        .,;'';;,..,;;;,,,,,.''';;,..
        ,,''                    '';;;;,;''
    ;'    ,;@@;'  ,@@;, @@, ';;;@@;,;';.
    ''  ,;@@@@@'  ;@@@@; ''    ;;@@@@@;;;;
        ;;@@@@@;    '''     .,,;;;@@@@@@@;;;
        ;;@@@@@@;           , ';;;@@@@@@@@;;;.
        '';@@@@@,.  ,   .   ',;;;@@@@@@;;;;;;
            .   '';;;;;;;;;,;;;;@@@@@;;' ,.:;'
            ''..,,     ''''    '  .,;'
                ''''''::''''''''
               
       _____ ____  __     ________  ________
      / ___// /\ \/ /    / ____/\ \/ / ____/
      \__ \/ /  \  /    / __/    \  / __/   
     ___/ / /___/ /    / /___    / / /___   
    /____/_____/_/    /_____/   /_/_____/ 
    """
    print(logo)

def collect_trufflehog_results(image):
    try:
        logger.debug(f"Running Trufflehog on {image}")
        trufflehog = TruffleHog()
        return trufflehog.run_trufflehog(image)
    except Exception as e:
        logger.debug(f"Trufflehog scan failed for {image}: {e}")
        return []
    
def start_processes(results, executor):
    futures = []
    for image in results:
        image_id = image["id"]
        logger.debug(f"Submitting scan on {image_id}")
        future = executor.submit(collect_trufflehog_results, image_id)
        futures.append((image_id, future))
    return futures

def insert_results(results, image_id, es, index):
    logger.debug(f"Adding {len(results)} results from {image_id} into elastic")
    actions = [
        {"_index": index, "_source": result}
        for result in results
    ]
    helpers.bulk(es, actions)
    
def main(args):
    es, _ = start_elastic()
    if args.only_kibana:
        start_kibana()
        return
    elif args.kibana:
        start_kibana()

    recent_docker_images = dockerhub_source()
    results = recent_docker_images["routes/_layout.search"]["data"]["searchResults"]["results"]
        
    executor = BoundedProcessPool()
    futures = start_processes(results, executor)
    
    logger.debug("Waiting for all workers to finish")
    try:
        for image_id, future in futures:
            try:
                trufflehog_results = future.result()
            except Exception as exc:
                logger.debug(f"Trufflehog scan failed for {image_id}: {exc}")
                continue

            if not trufflehog_results:
                continue

            insert_results(trufflehog_results, image_id, es, "trufflehog-findings")
    finally:
        executor.shutdown(wait=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A package scanner")

    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-logo", action="store_true", help="Hide the logo on startup")
    parser.add_argument("--kibana", action="store_true", help="Starts Kibana automatically")
    parser.add_argument("--only-kibana", action="store_true", help="Starts Kibana automatically")

    args = parser.parse_args()

    logger = logging.getLogger("sly-eye")

    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO
    else:
        level = logging.CRITICAL + 10

    coloredlogs.install(level=level, logger=logger, fmt="%(asctime)s [%(levelname)s] %(message)s")

    if not args.no_logo:
        display_logo()

    logger.debug("Starting sly-eye")
    main(args)
