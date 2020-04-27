import logging
from django.conf import settings
from slack import WebClient
from ..utils import register_slack_command, register_slack_action
from slackblocks import *

logger = logging.getLogger("slackbot")


def send_modal(state, view):
    res = settings.SLACK_CLIENT.views_open(
        trigger_id=state.trigger_id,
        view=make_modal(state, title="Loading...", blocks=[SectionBlock("Loading...")]),
    )

    state.ts = res["view"]["id"]

    settings.SLACK_CLIENT.views_update(view_id=state.ts, view=view)


def get_modal_state(payload):
    modal_state = {}
    values = payload["view"].get("state", {}).get("values", {})
    for key in values:
        for action_id in values[key]:
            modal_state[action_id] = values[key][action_id]
    return modal_state
