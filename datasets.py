from config import TRUENAS_ROOT_URL, MOUNT_PATH
from helpers import compare_dirs, copy_dir, delete_dir
from logger import logger
from truenas_api import TrueNASClient

import glob
import os
import subprocess


class Dataset:
    def __init__(self,
                 id: str,
                 path: str,
                 pool: str,
                 threshold: int,
                 backup_destination=None,
                 backup_targets: list = []):
        self.id = id
        self.path = path
        self.pool = pool
        self.threshold = threshold
        self.backup_destination = backup_destination
        self.backup_targets = backup_targets
        logger.info(self.__dict__)

    def check_connection(self):
        ls = glob.glob(MOUNT_PATH + '/*')
        for x in ls:
            if x.split('server=')[1] == (f"{TRUENAS_ROOT_URL},"
                                         f"share={self.id}"):
                return True
        return False

    def connect(self):
        if not self.check_connection():
            logger.info(f"{self.id} not yet mounted. Attempting to mount.")
            cmd = subprocess.run(
                f"gio mount smb://{TRUENAS_ROOT_URL}/{self.id}".split(" "),
                capture_output=True)
            if cmd.returncode == 0:
                logger.info("Mounted successfully")
                return True
            else:
                logger.warn(f"Failed to mount {self.id}: {cmd.stderr}")
                return False
        logger.info(f"{self.id} already mounted. Skipping.")
        return True

    def used_space(self):
        client = TrueNASClient()
        return client.get_used_space_gb(self.pool)

    def over_threshold(self):
        logger.info(f"{self.id} - used space: {self.used_space()}")
        logger.info(f"{self.id} - threshold: {self.threshold}")
        return self.used_space() > self.threshold

    def has_sufficient_space(file_size):
        pass


class FrigateBackup(Dataset):
    def purge_old_recordings(self):
        if not self.connect():
            logger.warn(f"{self.id} not connected. Skipping purge.")
            return
        over_threshold = self.over_threshold()
        if over_threshold:
            logger.warn(f"{self.id} over threshold. Purging old files.")
        while over_threshold:
            path = (f"{MOUNT_PATH}/smb-share:server="
                    f"{TRUENAS_ROOT_URL},share={self.id}/recordings")
            files = sorted(os.listdir(path))
            target_file = files[0]
            logger.info(f"Deleting {target_file}")
            delete_dir(f"{path}/{target_file}")
            over_threshold = self.over_threshold()
        logger.info(f"{self.id} under threshold.")


class Frigate(Dataset):
    def run_backup(self):
        if any([
            not self.connect(),
            not self.over_threshold(),
            not self.backup_destination.connect(),
            self.backup_destination.over_threshold()
        ]):
            logger.info("Frigate not in viable backup state. Skipping")
            return
        self.backup_recordings()

    def backup_recordings(self):
        logger.info("Starting backup for frigate")
        over_threshold = self.over_threshold()
        failed_attempts = 0
        files_backed_up_successfully = []
        files_failed_to_backup = []
        while over_threshold and failed_attempts < 2:
            primary_dir = (f"{MOUNT_PATH}/smb-share:server={TRUENAS_ROOT_URL},"
                           f"share={self.id}/recordings")
            backup_dir = (f"{MOUNT_PATH}/smb-share:server={TRUENAS_ROOT_URL},"
                          f"share={self.backup_destination.path}/recordings")
            files_to_backup, files_wrong_size = compare_dirs(
                primary_dir,
                backup_dir)
            if len(files_to_backup) == 0:
                logger.warn(f"{self.id}: no files found for backup.")
                continue

            logger.info(f"files needing backup: {sorted(files_to_backup)}")
            logger.info(f"files with mismatched sizes: {files_wrong_size}")

            backup_target = sorted(files_to_backup)[0]
            logger.info(f"backing up {backup_target}")
            copy_dir(f"{primary_dir}/{backup_target}",
                     f"{backup_dir}/{backup_target}")
            logger.info("done")

            if any([
                    backup_target in compare_dirs(
                        primary_dir,
                        backup_dir)[0],
                    backup_target in compare_dirs(
                        primary_dir,
                        backup_dir)[1]
                    ]):
                logger.error(f"backup of {backup_target} failed")
                files_failed_to_backup.append(backup_target)
                failed_attempts += 1
                continue

            logger.info(f"backed up {backup_target} successfully")
            logger.info(f"deleting {backup_target} from primary folder")
            delete_dir(f"{primary_dir}/{backup_target}")
            if backup_target in compare_dirs(
                        primary_dir,
                        backup_dir)[0]:
                files_failed_to_backup.append(backup_target)
                failed_attempts += 1
                continue

            files_backed_up_successfully.append(backup_target)
            over_threshold = self.over_threshold()
        logger.info((f"Files backed up successfully ({self.id}):"
                     f"{files_backed_up_successfully}"))
        if len(files_failed_to_backup) > 0:
            logger.error((f"Files failed to back up ({self.id}):"
                          f"{files_failed_to_backup}"))


frigate_backup = FrigateBackup(
                id="frigate-backup",
                path="frigate-backup",
                pool="backup",
                threshold=3300)

frigate = Frigate(
                id="frigate",
                path="frigate",
                pool="cctv",
                threshold=700,
                backup_destination=frigate_backup,
                backup_targets=["recordings", "clips"])
