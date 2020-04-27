import json
from typing import Union, List, Optional
from .blocks import Text, Block
from workspaces.utils import SlackState


def make_modal(
    state: SlackState,
    title: Union[str, Text],
    blocks: List[Block],
    action_id: Optional[str] = None,
    value: Optional[str] = None,
    submit: Optional[Union[Text, str]] = "Confirm",
    close: Optional[Union[Text, str]] = "Cancel",
):
    return {
        "type": "modal",
        "title": Text.to_text(title, force_plaintext=True)._resolve(),
        "submit": Text.to_text(submit, force_plaintext=True)._resolve(),
        "close": Text.to_text(close, force_plaintext=True)._resolve(),
        "blocks": repr(blocks),
        "private_metadata": json.dumps(
            {
                "channel_id": state.channel.id,
                "action_id": action_id,
                "value": value,
                "view_id": state.ts,
            }
        ),
    }
