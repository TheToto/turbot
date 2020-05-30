import logging

from slackblocks import (
    SectionBlock,
    ContextBlock,
    Image,
    ExternalSelect,
    TextInput,
    InputBlock,
    Option,
)
from turbot import settings
from workspaces.modal import send_modal, get_modal_state, make_modal
from workspaces.utils import (
    register_slack_action,
    register_slack_command,
    send_message,
)

logger = logging.getLogger("slackbot")


def get_report_blocks(login, text, author=None):
    blocks = [
        SectionBlock(
            f"Report `{login}`:\n{text}",
            accessory=Image(
                image_url=settings.PHOTO_FSTRING_SQUARE.format(login), alt_text=login
            ),
        ),
        ContextBlock(f"*By: {author.slack_username}*"),
    ]
    return repr(blocks)


@register_slack_command("/report")
def report(state):
    splitted = state.text.split(maxsplit=1)
    login = splitted[0] if len(splitted) > 0 else None
    report_text = splitted[1] if len(splitted) > 1 else None

    blocks = [
        InputBlock(
            "Choose a student",
            element=ExternalSelect(
                "Type a login",
                "report.student",
                initial_option=Option(login, login) if login else None,
            ),
        ),
        InputBlock(
            "Describe the issue",
            element=TextInput(
                "report.description", initial_value=report_text, multiline=True
            ),
        ),
    ]

    send_modal(
        state,
        make_modal(
            state, title="Report a student", blocks=blocks, action_id="report.post"
        ),
    )


@register_slack_action("report.post")
def post_report(state):
    if state.type == "view_submission":
        modal_state = get_modal_state(state.payload)
        login = modal_state["report.student"]["selected_option"]["value"]
        description = modal_state["report.description"]["value"]
        blocks = get_report_blocks(login, description, state.user)
        send_message(state, text=f"{state.user} reported {login}", blocks=blocks)
