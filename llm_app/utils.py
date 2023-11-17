import logging

import pathway as pw
import requests

logfun = logging.info


def send_slack_alerts(
    message: pw.ColumnReference, slack_alert_channel_id, slack_alert_token
):
    def send_slack_alert(key, row, time, is_addition):
        if not is_addition:
            return
        alert_message = row[message.name]
        logfun(alert_message)
        requests.post(
            "https://slack.com/api/chat.postMessage",
            data="text={}&channel={}".format(alert_message, slack_alert_channel_id),
            headers={
                "Authorization": "Bearer {}".format(slack_alert_token),
                "Content-Type": "application/x-www-form-urlencoded",
            },
        ).raise_for_status()

    pw.io.subscribe(message._table, send_slack_alert)
