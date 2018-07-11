from os import remove
from os.path import exists


def remove_files_from_list(rm_list):
    for rmfile in rm_list:
        if exists(rmfile):
            remove(rmfile)