## How to run the project

To run the project, you will need
- OpenAI API Key
- (Optional) Google Drive folder and Google Service account

To use OpenAI API Key in the app, create `.env` file and put `OPENAI_API_KEY=sk-...` in it.
You can also set it in the `app.py` while initializing the embedder and chat instances.

```python
chat = llms.OpenAIChat(api_key='sk-...', ...)

embedder = embedders.OpenAIEmbedder(api_key='sk-...', ...)
```

The default version of the app uses local folder `data` as the source of documents. However, you can use any other pathway supported connector. For instance, to add a Google Drive folder as another source, uncomment the following code in the `app.py` and follow the steps below to learn how to set up your Service Account.

```python
drive_folder = pw.io.gdrive.read(
    object_id="YOUR FOLDER ID",
    with_metadata=True,
    service_user_credentials_file="secret.json",
    refresh_interval=30,
)

data_sources.append(drive_folder)
```

Before running the app, you will need to give the app access to the Google Drive folder, we follow the steps below.

In order to access files on your Google Drive from the Pathway app, you will need a Google Cloud project and a service user.

### Create a new project in the Google API console:

- Go to [https://console.cloud.google.com/projectcreate](https://console.cloud.google.com/projectcreate) and create new project
- Enable Google Drive API by going to [https://console.cloud.google.com/apis/library/drive.googleapis.com](https://console.cloud.google.com/apis/library/drive.googleapis.com), make sure the newly created project is selected in the top left corner
- Configure consent screen:
  - Go to [https://console.cloud.google.com/apis/credentials/consent](https://console.cloud.google.com/apis/credentials/consent)
  - If using a private Gmail, select "External", and go next.
  - Fill required parameters: application name, user support, and developer email (your email is fine)
  - On the next screen click "Add or remove scopes" search for "drive.readonly" and select this scope
  - Save and click through other steps
- Create service user:

  - Go to [https://console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
  - Click "+ Create credentials" and create a service account
  - Name the service user and click through the next steps
- Generate service user key:
  - Once more go to [https://console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials) and click on your newly created user (under Service Accounts)
  - Go to "Keys", click "Add key" -> "Create new key" -> "JSON"
  
  A JSON file will be saved to your computer.

Rename this JSON file to `secrets.json` and put it under `examples/pipelines/drive_alert` next to `app.py` so that it is easily reachable from the app.

You can now share desired Google Drive resources with the created user.
Note the email ending with `gserviceaccount.com` we will share the folder with this email.

Once you've done it, you will need an ID of some file or directory. You can obtain it manually by right-clicking on the file -> share -> copy link. It will be part of the URL.

[https://drive.google.com/file/d/[FILE_ID]/view?usp=drive_link](https://drive.google.com/file/d/%5BFILE_ID%5D/view?usp=drive_link)

For folders,
First, right-click on the folder and click share, link will be of the format: [https://drive.google.com/drive/folders/[folder_id]?usp=drive_link](https://drive.google.com/drive/folders/%7Bfolder_id%7D?usp=drive_link)
Copy the folder_id from the URL.
Second, click on share and share the folder with the email ending with `gserviceaccount.com`