import os
import subprocess
import time

from dotenv import load_dotenv

load_dotenv()

remote_name = os.environ.get("REMOTE_NAME", "drive")  # rclone config name for drive
remote_folder = os.environ.get("REMOTE_FOLDER", "magic-cola")  # folder under the drive
tracked_file = os.environ.get("TRACKED_FILE", "staging/campaign.docx")
local_folder = os.environ.get("LOCAL_FOLDER", "local-drive/")


def parse_rclone_output(output):
    file_info = {}
    lines = output.split("\n")
    for line in lines:
        if line.strip():
            parts = line.split()
            size, edit_time, filename = (
                int(parts[0]),
                parts[1] + " " + parts[2],
                parts[3:],
            )
            file_info[filename[-1]] = {"size": size, "edit_time": edit_time}
    return file_info


fetch_folder = remote_name + ":" + remote_folder
print(f"syncing {fetch_folder} with ")

prev_edit = 0

while True:
    time.sleep(2)
    check_process = subprocess.Popen(
        ["rclone", "lsl", fetch_folder],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    check_stdout, check_stderr = check_process.communicate()

    file_info = parse_rclone_output(check_stdout)
    from datetime import datetime

    print(file_info)

    if prev_edit != file_info[tracked_file]["edit_time"]:
        info = file_info[tracked_file]

        st = "".join(info["edit_time"].split(".")[:-1])
        print(st)
        parsed_timestamp = datetime.strptime(st, "%Y-%m-%d %H:%M:%S")

        time_tuple = parsed_timestamp.timetuple()

        timestamp_in_seconds = time.mktime(time_tuple)
        print(timestamp_in_seconds)
        print(time.time() - timestamp_in_seconds)

        if time.time() - timestamp_in_seconds <= 4:
            print("sleeping")
            time.sleep(4)
            print("syncing")
            sync_process = subprocess.Popen(
                [
                    "rclone",
                    "sync",
                    fetch_folder,
                    local_folder,
                    "--include",
                    "*.docx",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            sync_stdout, sync_stderr = sync_process.communicate()
        else:
            time.sleep(4)
            print("syncing")
            sync_process = subprocess.Popen(
                [
                    "rclone",
                    "sync",
                    fetch_folder,
                    local_folder,
                    "--include",
                    "*.docx",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
            sync_stdout, sync_stderr = sync_process.communicate()

            print("rclone sync stdout:", sync_stdout)
            print("rclone sync stderr:", sync_stderr)
            time.sleep(8)

        check_process = subprocess.Popen(
            ["rclone", "lsl", fetch_folder],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        check_stdout, check_stderr = check_process.communicate()
        file_info = parse_rclone_output(check_stdout)
        prev_edit = file_info[tracked_file]["edit_time"]
