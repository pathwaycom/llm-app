## How to run the project
    
For this demo, Slack notification is optional and notifications will be printed if no Slack API keys are provided. See: [Slack Apps](https://api.slack.com/apps) and [Getting a token](https://api.slack.com/tutorials/tracks/getting-a-token)

Before running the app, you will need to give the app access to Google Drive folder, we follow the steps below.

In order to access files on your Google Drive from the Pathway app, you will need a google cloud project and a service user.

### Create new project in Google API console:

- Go to [https://console.cloud.google.com/projectcreate](https://console.cloud.google.com/projectcreate) and create new project
- Enable Google Drive API by going to [https://console.cloud.google.com/apis/library/drive.googleapis.com](https://console.cloud.google.com/apis/library/drive.googleapis.com), make sure newly created project is selected in top left corner
- Configure consent screen:
  - Go to [https://console.cloud.google.com/apis/credentials/consent](https://console.cloud.google.com/apis/credentials/consent)
  - If using a private Gmail, select "External", go next.
  - Fill required parameters: application name, user support and developer email (your email is fine)
  - On the next screen click "Add or remove scopes" and search for "drive.readonly" and select this scope
  - Save and click through other steps
- Create service user:
Go to [https://console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials)
Click "+ Create credentials" and create service account
Name service user and click through next steps
- Generate service user key:
Once more go to [https://console.cloud.google.com/apis/credentials](https://console.cloud.google.com/apis/credentials) and click on your newly created user (under Service Accounts)
Go to "Keys", click "Add key" -> "Create new key" -> "JSON"
JSON file will be saved to your computer.

Rename this JSON file to `secrets.json` and put it under `llm-app/examples/pipelines/drive_alert` so that it is easily reachable from app.

You can now share desired Google Drive resources with the created user.
Note the email ending with `gserviceaccount.com` we will share the folder with this email.

Once you've done it, you will need an id of some file or directory. You can obtain it manually by right clicking on the file -> share -> copy link. It will be part of the URL.

[https://drive.google.com/file/d/[FILE_ID]/view?usp=drive_link](https://drive.google.com/file/d/%5BFILE_ID%5D/view?usp=drive_link)

For folders,
First, right click on folder and click share, link will be of the format: [https://drive.google.com/drive/folders/[folder_id]?usp=drive_link](https://drive.google.com/drive/folders/%7Bfolder_id%7D?usp=drive_link)
Copy the folder_id from the URL.
Second, click on share and share the folder with the email ending with `gserviceaccount.com`

Usage:
First, set you env variables in .env file placed in root of repo
```bash
OPENAI_API_KEY=sk-...
PATHWAY_REST_CONNECTOR_HOST=127.0.0.1
PATHWAY_REST_CONNECTOR_PORT=8181
SLACK_ALERT_CHANNEL_ID=
SLACK_ALERT_TOKEN=
REMOTE_NAME=<your config name from rclone>
REMOTE_FOLDER=magic-cola #  folder name under your google drive
FILE_OR_DIRECTORY_ID=staging/campaign.docx  # file or folder id that you want to track
GOOGLE_CREDS=secret.json #  file with your Google creds that you downloaded earlier 
```

### Run the project,

`poetry run ./run_examples.py drivealert`
or, if all dependencies are managed manually rather than using poetry
You can either
`python examples/pipelines/drivealert/app.py`
or
`python ./run_examples.py drivealert`

You can also run this example directly in the environment with llm_app installed.

To create alerts:
You can call the REST API:
curl --data '{
  "user": "user",
  "query": "When does the magic cola campaign start? Alert me if the start date changes."
}' http://localhost:8080/ | jq

Or start streamlit UI:
First go to examples/pipelines/drive_alert/ui directory with `cd examples/pipelines/drive_alert/ui/`
run `streamlit run server.py`