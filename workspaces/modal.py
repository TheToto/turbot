import json
import logging
from typing import List, Optional

from django.conf import settings

from slackblocks import SectionBlock, Union, Text, Block
from workspaces.utils import SLACK_ACTIONS, SlackState

logger = logging.getLogger("slackbot")


def make_modal(
    state: SlackState,
    title: Union[str, Text],
    blocks: List[Block],
    action_id: Optional[str] = None,
    value: Optional[str] = None,
    metadata: Optional[dict] = {},
    submit: Optional[Union[Text, str]] = "Confirm",
    close: Optional[Union[Text, str]] = "Cancel",
):
    private_metadata = {
        "channel_id": state.channel.id,
        "action_id": action_id,
        "value": value,
        "ts": state.ts,
        **get_private_metadata(state),
        **metadata,
    }

    return {
        "type": "modal",
        "title": Text.to_text(title, force_plaintext=True)._resolve(),
        "submit": Text.to_text(submit, force_plaintext=True)._resolve(),
        "close": Text.to_text(close, force_plaintext=True)._resolve(),
        "blocks": repr(blocks),
        "private_metadata": json.dumps(private_metadata),
    }


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


def get_private_metadata(state):
    return json.loads(state.payload.get("view", {}).get("private_metadata", "{}"))


def update_modal(state, view):
    private_metadata = get_private_metadata(state)
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


def dispatch_modal_actions(state):
    for action in state.payload["actions"]:
        action_id = action["action_id"]
        if action_id not in SLACK_ACTIONS:
            return logger.error(f"No action {action_id}")
        for event_fun in SLACK_ACTIONS[action_id]:
            event_fun(state)
