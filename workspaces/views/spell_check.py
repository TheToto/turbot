import json
import logging

from django.http import HttpResponse, JsonResponse

from turbot import settings
from workspaces.utils import (
    SLACK_ACTIONS,
    get_request_entities,
    SLACK_EVENTS,
    register_slack_event,
)

from subprocess import check_output, STDOUT

logger = logging.getLogger("slackbot")


def lauch_leodagan(input_str):
    result = check_output(
        ["python", "submodule/leodagan/leodagan.py", "-q"],
        stderr=STDOUT,
        input=input_str.encode(),
    )
    return result


@register_slack_event("app_mention")
def spell_check(payload):
    if "thread_ts" in payload["event"]:
        query = settings.SLACK_CLIENT.conversations_history(
            channel=payload["event"]["channel"],
            latest=payload["event"]["thread_ts"],
            limit=1,
            inclusive="true",
        )
        message = query["messages"][0]
        logger.debug(message)
        texts_to_test = []
        for block in message["blocks"]:
            for element in block["elements"]:
                if element["type"] == "rich_text_preformatted":
                    current_text = ""
                    # Slack has the bad idea to split code blocks
                    for e in element["elements"]:
                        current_text += e["text"]
                    texts_to_test.append(current_text)
        logger.debug(texts_to_test)
        for text in texts_to_test:
            leodagan_result = lauch_leodagan(text).decode("utf-8")
            if not leodagan_result:
                leodagan_result = "Pas de problèmes dans ce message"
            logger.debug(leodagan_result)
            logger.debug(
                settings.SLACK_CLIENT.chat_postMessage(
                    text=leodagan_result,
                    channel=payload["event"]["channel"],
                    thread_ts=payload["event"]["thread_ts"],
                )
            )

        return HttpResponse(status=200)
