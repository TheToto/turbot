import logging

import requests
from django.http import HttpResponse, JsonResponse

from slackblocks import (
    SectionBlock,
    ImageBlock,
    ActionsBlock,
    Button,
    ContextBlock,
)
from turbot import settings
from workspaces.models import User
from workspaces.utils import register_slack_action

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
