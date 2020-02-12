import json
import logging

import requests
from django.http import HttpResponse, JsonResponse

from slackblocks import (
    SectionBlock,
    ActionsBlock,
    Button,
    ContextBlock,
    Image,
)
from turbot import settings
from workspaces.models import User
from workspaces.utils import register_slack_action, get_request_entities

logger = logging.getLogger("slackbot")


def get_report_blocks(login, text, author=None):
    blocks = [
        SectionBlock(
            f"Report `{login}`:\n{text}",
            accessory=Image(
                image_url=settings.PHOTO_FSTRING_SQUARE.format(login), alt_text=login
            ),
        )
    ]
    if not author:
        response = requests.head(settings.PHOTO_FSTRING_SQUARE.format(login))
        if response.status_code != 200:
            blocks.append(SectionBlock(":warning: Login not found"))

        blocks.append(
            ActionsBlock(
                Button(
                    text="Send report",
                    action_id="report.post",
                    value=json.dumps({"login": login, "text": text}),
                )
            )
        )
    else:
        blocks.append(ContextBlock(f"*By: {author.slack_username}*"))

    return repr(blocks)


def report(request):
    _, _, _ = get_request_entities(request)
    login, report_text = request.POST["text"].split(maxsplit=1)
    login = login.lower()
    return JsonResponse(
        {"text": "Report preview", "blocks": get_report_blocks(login, report_text)}
    )


@register_slack_action("report.post")
def post_report(payload):
    author = User(payload["user"]["id"])
    values = json.loads(payload["actions"][0]["value"])
    login = values["login"]
    text = values["text"]

    blocks = get_report_blocks(login, text, author)
    logger.debug(blocks)

    logger.debug(
        settings.SLACK_CLIENT.chat_postMessage(
            text=f"{author} reported {login}",
            channel=payload["channel"]["id"],
            blocks=blocks,
        )
    )
    requests.post(payload["response_url"], json={"delete_original": "true",})
    return HttpResponse(status=200)
