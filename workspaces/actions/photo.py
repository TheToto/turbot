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
from workspaces.utils import (
    register_slack_action,
    register_slack_command,
    send_ephemeral,
    send_message,
    SlackState,
)

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


@register_slack_command("/cri-photo")
def photo(state):
    photo_slug = state.text.lower()
    response = requests.head(settings.PHOTO_FSTRING.format(photo_slug))
    if response.status_code != 200:
        return send_ephemeral(state, f"Login not found : {photo_slug}")

    send_ephemeral(
        state, f"Picture of {photo_slug}", get_photo_blocks(photo_slug, response.url)
    )


@register_slack_action("photo.post")
def post_photo(state: SlackState):
    stalker = state.user
    photo_slug = state.text

    blocks = get_photo_blocks(
        photo_slug, settings.PHOTO_FSTRING.format(photo_slug), stalker
    )

    send_message(state, text=f"Picture of {photo_slug}", blocks=blocks)
    requests.post(state.response_url, json={"delete_original": "true",})
