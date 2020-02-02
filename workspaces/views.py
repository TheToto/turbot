import logging
import requests

import json
from django.http import HttpResponse, JsonResponse

from slackblocks import (
    SectionBlock,
    Text,
    ImageBlock,
    ActionsBlock,
    Button,
    ContextBlock,
    Image,
)

from turbot import settings
from workspaces.models import User
from workspaces.utils import SLACK_ACTIONS, register_slack_action, get_request_entities

logger = logging.getLogger("slackbot")


def get_photo_blocks(photo_slug, url, stalker=None):
    blocks = [
        SectionBlock(text=f"*{photo_slug}*"),
        ImageBlock(image_url=url, alt_text=photo_slug, title=photo_slug),
    ]
    if not stalker:
        blocks.append(
            ActionsBlock(
                Button(text="Send to Channel", action_id="photo.post", value=photo_slug)
            )
        )
    else:
        blocks.append(ContextBlock(f"*Stalké Par: {stalker.slack_username}*"))

    return repr(blocks)


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


def oauth(request):
    return "ok"


def test(request):
    return "ok"


def action(request):
    payload = json.loads(request.POST["payload"])
    logger.debug(payload)
    action_name: str = payload["actions"][0]["action_id"]
    return SLACK_ACTIONS[action_name](payload)


def photo(request):
    photo_slug = request.POST["text"].lower()
    response = requests.head(settings.PHOTO_FSTRING.format(photo_slug))
    if response.status_code != 200:
        return HttpResponse(f"No such login : {photo_slug}")

    return JsonResponse(
        {
            "text": f"Picture of {photo_slug}",
            "blocks": get_photo_blocks(photo_slug, response.url),
        }
    )


@register_slack_action("photo.post")
def post_photo(payload):
    stalker = User(payload["user"]["id"])
    photo_slug = payload["actions"][0]["value"]

    blocks = get_photo_blocks(
        photo_slug, settings.PHOTO_FSTRING.format(photo_slug), stalker
    )

    logger.debug(blocks)

    logger.debug(
        settings.SLACK_CLIENT.chat_postMessage(
            text=f"Picture of {photo_slug}",
            channel=payload["channel"]["id"],
            blocks=blocks,
        )
    )
    requests.post(payload["response_url"], json={"delete_original": "true",})
    return HttpResponse(status=200)


def suffix(request):
    _, _, user = get_request_entities(request)
    user.suffix = request.POST["text"]
    user.save()
    return JsonResponse({"text": f"Saved !\nNew display : {user.slack_username}"})


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
