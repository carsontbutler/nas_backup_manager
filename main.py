from datasets import (frigate, frigate_backup)
from logger import logger


def main():
    logger.info("ProgramStart")

    logger.info("Checking if frigate-backup needs purging.")
    frigate_backup.purge_old_recordings()

    logger.info("Starting frigate backup")
    frigate.run_backup()


main()
