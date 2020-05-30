import logging
from django.conf import settings
from slack import WebClient
from ..utils import register_slack_command, register_slack_action
from slackblocks import *

logger = logging.getLogger("slackbot")


def send_modal(state, view, keep_view_id=False):
    if not keep_view_id:
        return settings.SLACK_CLIENT.views_open(trigger_id=state.trigger_id, view=view)

    res = settings.SLACK_CLIENT.views_open(
        trigger_id=state.trigger_id,
        view=make_modal(state, title="Loading...", blocks=[SectionBlock("Loading...")]),
    )

    view_id = res["view"]["id"]
    private_metadata = json.loads(view["private_metadata"])
    private_metadata["view_id"] = view_id
    view["private_metadata"] = json.dumps(private_metadata)

    settings.SLACK_CLIENT.views_update(view_id=view_id, view=view)


def update_modal(state, view):
    private_metadata = json.loads(payload["view"]["private_metadata"])
    view_id = private_metadata.get("view_id")
    if not view_id:
        return logger.error("No view_id for update modal !")

    settings.SLACK_CLIENT.views_update(view_id=view_id, view=view)


def get_modal_state(payload):
    modal_state = {}
    values = payload["view"].get("state", {}).get("values", {})
    for key in values:
        for action_id in values[key]:
            modal_state[action_id] = values[key][action_id]
    return modal_state
