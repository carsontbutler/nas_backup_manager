import os
import subprocess
from logger import logger


def to_gb(input):
    size, unit = float(input[:-1]), input[-1]
    if unit.upper() == 'T':
        return round(size * 1000, 2)
    elif unit.upper() == 'G':
        return size
    elif unit.upper() == 'M':
        return size * .001
    elif unit.upper() == 'K':
        return round(size * .000001, 2)


def copy_dir(dir_to_copy, destination):
    res = subprocess.run(
        f"scp -r {dir_to_copy} {destination}"
        .split(' '), capture_output=True)
    if res.stderr:
        logger.info((f"Failed to backup {dir_to_copy}."
                     f"Exception: {res.stderr}"))
    else:
        logger.info(f"Moved {dir_to_copy} to {destination}")


def delete_dir(dir_to_delete):
    res = subprocess.run(
        f"rm -r {dir_to_delete}"
        .split(' '), capture_output=True)
    if res.stderr:
        logger.info((f"Failed to delete {dir_to_delete}."
                     f"Exception: {res.stderr}"))
    else:
        logger.info(f"Deleted {dir_to_delete} successfully")


def unique_files(dir1, dir2):
    """Shows unique files/dirs in the top level only"""
    dir1_files = os.listdir(dir1)
    dir2_files = os.listdir(dir2)
    dir1_unique_files = [x for x in dir1_files if x not in dir2_files]
    dir2_unique_files = [x for x in dir2_files if x not in dir1_files]
    return dir1_unique_files, dir2_unique_files


def compare_dirs(dir1, dir2):
    """
    Compares top level files in primary (dir1) to backup (dir2) and returns:
        files_without_backups = [files that exist in dir1 but not dir2]
        files_wrong_size = [files that exist in both but are different size]
    """
    d1 = {x: os.path.getsize(f"{dir1}/{x}") for x in os.listdir(dir1)}
    d2 = {x: os.path.getsize(f"{dir2}/{x}") for x in os.listdir(dir2)}

    files_without_backups = []
    files_wrong_size = []

    for k, v in d1.items():
        if d2.get(k) is None:
            files_without_backups.append(k)
        elif v != d2.get(k):
            files_wrong_size.append(k)
    return files_without_backups, files_wrong_size
