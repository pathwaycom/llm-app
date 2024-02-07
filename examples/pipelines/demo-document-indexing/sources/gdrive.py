from os.path import dirname, realpath

import pathway.io.gdrive as gdrive_connector

from .common import FILE_SIZE_LIMIT

GDRIVE_CONFIG = {
    "object_id": "1cULDv2OaViJBmOfG5WB0oWcgayNrGtVs",
    "service_user_credentials_file": f"{realpath(dirname(__file__))}/secrets/gdrive/gdrive_indexer.json",
    "refresh_interval": 5,
}


def get_table():
    gdrive_table = gdrive_connector.read(
        **GDRIVE_CONFIG,
        with_metadata=True,
        object_size_limit=FILE_SIZE_LIMIT,
    )
    return gdrive_table
