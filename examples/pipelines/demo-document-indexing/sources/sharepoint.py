import os
from os.path import dirname, realpath

from pathway.xpacks.connectors import sharepoint as sharepoint_connector

from .common import FILE_SIZE_LIMIT

SHAREPOINT_MUTABLE_COLLECTION_PATH = "Shared Documents/IndexerSandbox"

SHAREPOINT_SITE_CONFIG = {
    "url": "https://navalgo.sharepoint.com/sites/ConnectorSandbox",
    "tenant": os.environ["SHAREPOINT_TENANT"],
    "client_id": os.environ["SHAREPOINT_CLIENT_ID"],
    "cert_path": f"{realpath(dirname(__file__))}/secrets/sharepoint/sharepointcert.pem",
    "thumbprint": os.environ["SHAREPOINT_THUMBPRINT"],
    "refresh_interval": 5,
}


def get_table():
    sharepoint_table = sharepoint_connector.read(
        **SHAREPOINT_SITE_CONFIG,
        root_path=SHAREPOINT_MUTABLE_COLLECTION_PATH,
        with_metadata=True,
        object_size_limit=FILE_SIZE_LIMIT,
    )
    return sharepoint_table
