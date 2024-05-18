from datasets import (frigate)
from logger import logger


def main():
    logger.info("ProgramStart")
    logger.info("Starting frigate backup")
    frigate.run_backup()


main()
