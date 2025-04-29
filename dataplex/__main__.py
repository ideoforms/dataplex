import logging
import argparse

from .dataplex import Dataplex

logger = logging.getLogger(__name__)

if __name__ == "__main__":
    parser = argparse.ArgumentParser("Run the dataplex I/O server")
    parser.add_argument("--verbose", "-v", help="Verbose output", action="store_true")
    parser.add_argument("--quiet", "-q", help="Quiet output", action="store_true")
    parser.add_argument("-c", "--config-file", type=str, help="Path to JSON config file", default="config/config.json")
    args = parser.parse_args()

    log_level = "INFO"
    if args.quiet:
        log_level = "WARNING"
    elif args.verbose:
        log_level = "DEBUG"
    logging.basicConfig(level=log_level, format='%(asctime)s %(name)-24s %(levelname)-8s %(message)s')

    server = Dataplex(config_file=args.config_file)
    server.run()
