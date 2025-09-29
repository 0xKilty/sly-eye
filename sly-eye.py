import logging
import coloredlogs
import argparse
from elasticsearch import helpers

from src.sourcing.dockerhub import dockerhub_source
from src.scanning.trufflehog import run_trufflehog
from src.storing.elastic import start_elastic

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

    recent_docker_images = dockerhub_source()
    results = recent_docker_images["routes/_layout.search"]["data"]["searchResults"]["results"]
    
    for image in results:
        trufflehog_results = run_trufflehog(image["id"])

        logger.debug(f"Adding {len(trufflehog_results)} results into elastic")
        actions = [
            {"_index": "trufflehog-findings", "_source": result}
            for result in trufflehog_results
        ]

        helpers.bulk(es, actions)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A package scanner")

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--no-logo", action="store_true", help="Hide the logo on startup")
    parser.add_argument("--kibana", action="store_true", help="Starts Kibana automatically")

    args = parser.parse_args()

    logger = logging.getLogger("sly-eye")

    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO
    else:
        level = logging.CRITICAL + 10 #  turns off logging

    coloredlogs.install(level=level, logger=logger, fmt="%(asctime)s [%(levelname)s] %(message)s")

    if not args.no_logo:
        display_logo()

    logger.debug("Starting sly-eye")
    main(args)