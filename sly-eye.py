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
    
def main(args):
    es, _ = start_elastic()
    if args.only_kibana:
        start_kibana()
        return
    elif args.kibana:
        start_kibana()

    recent_docker_images = dockerhub_source()
    results = recent_docker_images["routes/_layout.search"]["data"]["searchResults"]["results"]
    
    trufflehog = TruffleHog()
    executor = BoundedProcessPool()

    def run_trufflehog_insert_results(image):
        try:
            trufflehog_results = trufflehog.run_trufflehog(image)
            logger.debug(f"Adding {len(trufflehog_results)} results from {image} into elastic")
            actions = [
                {"_index": "trufflehog-findings", "_source": result}
                for result in trufflehog_results
            ]
            helpers.bulk(es, actions)
        except Exception as e:
            logger.exception(f"Trufflehog scan failed for {image}: {e}")
    
    for image in results:
        logger.debug(f"Submitting scan on {image['id']}")
        executor.submit(run_trufflehog_insert_results, image["id"])

    logger.debug("Waiting for all threads to finish")
    executor.shutdown(wait=True)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A package scanner")

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
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