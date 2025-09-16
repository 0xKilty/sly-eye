import logging
import coloredlogs
import argparse

def main(args):
    pass

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="A package scanner")

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose mode")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")

    args = parser.parse_args()

    logger = logging.getLogger("sly-eye")

    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO
    else:
        level = logging.CRITICAL + 10 #  turns off logging

    coloredlogs.install(level=level, logger=logger, fmt="%(asctime)s [%(levelname)s] %(message)s")

    main(args)