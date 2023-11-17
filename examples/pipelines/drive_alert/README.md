## How to run the project

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

### Setup Slack notifications:

For this demo, Slack notifications are optional and notifications will be printed if no Slack API keys are provided. See: [Slack Apps](https://api.slack.com/apps) and [Getting a token](https://api.slack.com/tutorials/tracks/getting-a-token).
Your Slack application  will need at least `chat:write.public` scope enabled.

### Setup environment:
First, set your env variables in the .env file placed in the root of the repo.

```bash
OPENAI_API_KEY=sk-...
SLACK_ALERT_CHANNEL_ID=  # If unset, alerts will be printed to the terminal
SLACK_ALERT_TOKEN=
FILE_OR_DIRECTORY_ID=  # file or folder ID that you want to track that we have retrieved earlier
GOOGLE_CREDS=examples/pipelines/drive_alert/secrets.json  # Default location of Google Drive authorization secrets
```

### Run the project

Make sure you have installed poetry dependencies with `--extras unstructured`. 

```bash
poetry install --with examples --extras unstructured
```

Run:

```bash
poetry run ./run_examples.py drivealert
```

If all dependencies are managed manually rather than using poetry, you can run either:

```bash
python examples/pipelines/drive_alert/app.py
```

or

```bash
python ./run_examples.py drivealert
```

You can also run this example directly in the environment with llm_app installed.

To create alerts:
You can call the REST API:

```bash
curl --data '{
  "user": "user",
  "query": "When does the magic cola campaign start? Alert me if the start date changes."
}' http://localhost:8080/ | jq
```

Or start streamlit UI:

First go to `examples/pipelines/drive_alert/ui` directory with `cd examples/pipelines/drive_alert/ui/`
and run:

```bash
streamlit run server.py
```