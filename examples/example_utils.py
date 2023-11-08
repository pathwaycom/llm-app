import os
import pwd
import time


def find_last_modified_file(directory) -> str:
    """These functions are meant to be replaced with functionality from Pathway"""
    """Retrieves last added or modified file path.

    Args:
        directory (str, Path): path of the directory for search

    Returns:
        path (str, Path): full path of the found last modified file
    """
    latest_file = None
    latest_time = 0

    if os.path.exists(directory) and os.path.isdir(directory):
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_time = os.path.getmtime(file_path)
                file_time_create = os.path.getctime(file_path)

                file_time = max(file_time_create, file_time)

                if file_time > latest_time:
                    latest_time = file_time
                    latest_file = file_path

        if latest_file is not None:
            return latest_file
        else:
            return None
    else:
        return None


def get_file_info(file_path) -> dict:
    """These functions are meant to be replaced with functionality from Pathway"""
    """Retrieves os info about a given file.

    Args:
        file_path (str, Path): path of the file

    Returns:
        response (dict): dict containing information about file
    """
    try:
        modification_time = os.path.getmtime(file_path)
        create_time = os.path.getctime(file_path)
        modified_time_str = time.ctime(modification_time)
        create_time_str = time.ctime(create_time)

        last_edit = max(modification_time, create_time)
        last_edit_time_str = time.ctime(last_edit)

        owner_id = os.stat(file_path).st_uid
        owner_name = pwd.getpwuid(owner_id).pw_name

        return {
            "File": file_path.split(os.sep)[-1],
            "Modified Time": modified_time_str,
            "Created Time": create_time_str,
            "Owner": owner_name,
            "Last Edit": last_edit_time_str,
        }
    except Exception as e:
        return {"Error": str(e)}
