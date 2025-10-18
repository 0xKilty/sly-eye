import logging
import coloredlogs
import argparse
import os
from elasticsearch import helpers
from concurrent.futures import as_completed, ProcessPoolExecutor

from src.sourcing.dockerhub import dockerhub_source
from src.sourcing.pypi import pypi_source, download_pypi_package

from src.scanning.trufflehog import TruffleHog
from src.scanning.semgrep import run_semgrep_on_wheel

from src.storing.elastic import start_elastic, stop_elastic

from src.searching.kibana import start_kibana

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
        trufflehog = TruffleHog()
        return trufflehog.run_trufflehog(image)
    except Exception:
        return []

def collect_pypi_results(package):
    file_path = download_pypi_package(package)
    semgrep_results = run_semgrep_on_wheel(file_path)
    # guarddog_results = run_guarddog_on_tarball(file_path)

    os.remove(file_path)
    return semgrep_results# , guarddog_results

def start_processes(targets, executor, collector):
    futures = {}
    for target in targets:
        logger.debug(f"Submitting {collector.__name__}({target!r})")
        future = executor.submit(collector, target)
        futures[future] = target
    return futures

def insert_results(results, image_id, es, index):
    logger.debug(f"Adding {len(results)} results from {image_id} into elastic")
    if not results:
        return
    actions = [
        {"_index": index, "_source": result}
        for result in results
    ]
    try:
        helpers.bulk(es, actions, chunk_size=100)
    except Exception as e:
        logger.error(f"Failed to insert results for {image_id}: {e}")
    
def main(args):
    es, container = start_elastic()
    if args.only_kibana:
        start_kibana()
        return
    elif args.kibana:
        start_kibana()

    max_workers = max(1, args.max_workers)
    executor = ProcessPoolExecutor(max_workers=max_workers)
    logger.debug(f"Process pool initialized with max_workers={max_workers}")

    if args.command == "docker":
        recent_docker_images = dockerhub_source()
        images_info = recent_docker_images["routes/_layout.search"]["data"]["searchResults"]["results"]
        image_names = [image["id"] for image in images_info]
        futures = start_processes(image_names, executor, collect_trufflehog_results)
    elif args.command == "pypi":
        recent_pypi_packages = pypi_source()
        packages = [entry.link for entry in recent_pypi_packages]
        for package in packages:
            results = collect_pypi_results(package)
            print(results)
        return
        # futures = start_processes(packages, executor, collect_pypi_results)
    else:
        raise ValueError(f"Invalid command type: {args.command}") # should never happen but just in case of a bit flip

    logger.debug("Waiting for all workers to finish")
    try:
        for future in as_completed(list(futures.keys())):
            target = futures[future]
            try:
                results = future.result()
            except Exception as e:
                logger.debug(f"Scan failed for {target}: {e}")
                continue

            if not results:
                continue

            insert_results(results, target, es, f"{args.command}-findings")
    finally:
        executor.shutdown(wait=True)
        stop_elastic(container)
        logger.debug("Cleaned up and exiting.")


if __name__ == "__main__":
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    common.add_argument("--no-logo", action="store_true", help="Hide the logo on startup")
    common.add_argument("--kibana", action="store_true", help="Starts Kibana automatically")
    common.add_argument("--only-kibana", action="store_true", help="Starts Kibana automatically")
    common.add_argument("--max-workers", type=int, default=4, help="Limit concurrent scans (default: 4)")

    parser = argparse.ArgumentParser(description="A package scanner", parents=[common])
    subparsers = parser.add_subparsers(dest="command", required=True)

    docker_parser = subparsers.add_parser("docker", parents=[common], help="Scan Docker images")
    pypi_parser = subparsers.add_parser("pypi", parents=[common], help="Scan PyPI packages")

    args, unknown = parser.parse_known_args()
    args = parser.parse_args()

    logger = logging.getLogger("sly-eye")

    if args.debug:
        level = logging.DEBUG
    else:
        level = logging.CRITICAL + 10

    coloredlogs.install(level=level, logger=logger, fmt="%(asctime)s [%(levelname)s] %(message)s")

    if not args.no_logo:
        display_logo()

    logger.debug("Starting sly-eye")
    main(args)
