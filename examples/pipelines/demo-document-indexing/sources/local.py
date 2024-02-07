import pathway.io.fs as filesystem_connector

FILESYSTEM_CONFIG = {
    "path": "files-for-indexing/",
    "format": "binary",
    "with_metadata": True,
}


def get_table():
    filesystem_table = filesystem_connector.read(**FILESYSTEM_CONFIG)
    return filesystem_table
