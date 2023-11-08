import logging
from typing import Any, Callable, TypeVar

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


TDedupe = TypeVar("TDedupe")
TSchema = TypeVar("TSchema")


def deduplicate(
    table: pw.Table[TSchema],
    *,
    col: pw.ColumnReference,
    instance: pw.ColumnReference = None,
    acceptor: Callable[[TDedupe, TDedupe], bool],
) -> pw.Table[TSchema]:
    """Deduplicates rows in `table` on `col` column using acceptor function.

    It keeps rows for which acceptor returned previous value

    Args:
        table (pw.Table[TSchema]): table to deduplicate
        col (pw.ColumnReference): column used for deduplication
        acceptor (Callable[[TDedupe, TDedupe], bool]): callback telling whether two values are different
        instance (pw.ColumnReference, optional): Group column for which deduplication will be performed separately.
            Defaults to None.

    Returns:
        pw.Table[TSchema]:
    """
    assert col.table == table
    assert instance is None or instance.table == table
    previous_states: dict[Any, TDedupe | None] = dict()

    # keeping state in Python, accessed by non-pure udf function. This is Pathway antipattern.
    # todo: refactor once we have proper differentiation operator

    @pw.udf
    def is_different_with_state(new_state: TDedupe, key: Any) -> bool:
        prev_state = previous_states.get(key, None)
        if prev_state is None:
            previous_states[key] = new_state
            return True
        are_different = acceptor(new_state, prev_state)
        if are_different:
            previous_states[key] = new_state
        return are_different

    return table.filter(is_different_with_state(col, instance) == True)  # noqa: E712
