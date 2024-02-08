# Realtime Document Indexing with Pathway

This is a basic service for a real-time document indexing pipeline powered by [Pathway](https://github.com/pathwaycom/pathway).

## Running the Example 🚀

This example spawns a lightweight webserver that accepts queries on three possible endpoints:
- `/v1/retrieve` to perform similarity search;
- `/v1/statistics` to get the basic stats about the indexer's health;
- `/v1/inputs` to retrieve the metadata of all files currently processed by the indexer.

Please refer to the Open API doc on Hosted Pipelines [website](https://cloud.pathway.com/) for the format of the requests to the endpoints.

This example can be run by executing `python main.py` in this directory. It has several command-line arguments:
- `--host` denoting the host, where the server will run. The default setting is `0.0.0.0`;
- `--port` denoting the port, where the server will accept requests. The default setting is `21401`;
- `--source-types` denoting comma-separated types of the sources to index. The options are: `local`, `gdrive`, and `sharepoint`. The `local` option indexes files from the `file-for-indexing/` folder that already has some exemplary documents. The `gdrive` and `sharepoint` options correspond to Google Drive and SharePoint respectively and are used in the hosted demo. Please note that they will require certain certificates and credentials to be read locally or from environment variables. The default setting is `local`.

## Adding Files to Index 💾
    
To start playing with this demo, you can either:

- Add a file to the `files-for-indexing/` folder if the local data source is used;
- ...or add one to the common SharePoint [site](https://navalgo.sharepoint.com/:f:/s/ConnectorSandbox/EgBe-VQr9h1IuR7VBeXsRfIBuOYhv-8z02_6zf4uTH8WbQ?e=YmlA05) or Google Drive [directory](https://drive.google.com/drive/u/0/folders/1cULDv2OaViJBmOfG5WB0oWcgayNrGtVs) if `sharepoint` and `gdrive` options are configured.

Then you can use the similarity search and stats endpoints, provided below.

## Capabilities 🛠️
    
The capabilities of the service include:
    
- Real-time document indexing from Microsoft 365 SharePoint, Google Drive, or a local directory;
- Similarity search by user query;
- Filtering by the metadata according to the condition given in [JMESPath format](https://jmespath.org/);
- Basic stats on the indexer's health.
    
Supported document formats include plaintext, pdf, docx, and HTML. For the complete list, please refer to the supported formats of the [unstructured](https://github.com/Unstructured-IO/unstructured) library.

In addition, this pipeline is capable of data removals: you can delete files and in a few seconds, a similarity search will undo the changes done to the index by their addition.

## Demo Limitations🚦
    
Please keep in mind the following constraints:
    
- The maximum supported file size is 4 MB and 100 KB of the plaintext is obtained after parsing. Anything of a greater size will be ignored by the indexer. This setting is controlled by the setting in the `sources.common` module;
- The files in the public shared in Google Drive and SharePoint spaces are removed within 15 minutes after their addition;
- You hold responsibility for the contents of the files you upload to the public spaces.
