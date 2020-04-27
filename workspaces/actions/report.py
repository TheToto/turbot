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
from workspaces.utils import (
    register_slack_action,
    register_slack_command,
    send_message,
    send_ephemeral,
)

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


@register_slack_command("/report")
def report(state):
    login, report_text = state.text.split(maxsplit=1)
    login = login.lower()
    send_ephemeral(
        state, text=f"Report preview", blocks=get_report_blocks(login, report_text)
    )


@register_slack_action("report.post")
def post_report(state):
    values = json.loads(state.text)
    login = values["login"]
    text = values["text"]

    blocks = get_report_blocks(login, text, state.user)

    send_message(state, text=f"{state.user} reported {login}", blocks=blocks)
    requests.post(state.response_url, json={"delete_original": "true",})
