import logging

from polls.actions import create_poll
from slackblocks import (
    TextInput,
    InputBlock,
    Option,
    Checkboxes,
    ActionsBlock,
    Button,
)
from workspaces.modal import (
    send_modal,
    get_modal_state,
    update_modal,
    dispatch_modal_actions,
    get_modal_metadata,
    make_modal,
)
from workspaces.utils import (
    register_slack_action,
    register_slack_command,
)

logger = logging.getLogger("slackbot")


def get_blocks(nb_choice):
    return [
        InputBlock("Title", block_id="title", element=TextInput("poll.title")),
        InputBlock(
            "Params",
            block_id="params",
            optional=True,
            element=Checkboxes(
                "poll.params",
                options=[
                    Option("Annoymous", "annon"),
                    Option("Open poll", "open"),
                    Option("Unique choice", "unique"),
                ],
            ),
        ),
        *(
            [
                InputBlock(
                    "Choice",
                    block_id=f"{i}",
                    element=TextInput(f"poll.choice{i}"),
                    optional=True,
                )
                for i in range(nb_choice)
            ]
        ),
        ActionsBlock(elements=Button("Add choice", "poll.build.add_choice")),
    ]


@register_slack_command("/poll-build")
@register_slack_action("poll.build")
def poll_builder(state):
    blocks = get_blocks(2)

    state.thread_ts = state.ts

    send_modal(
        state,
        make_modal(state, title="Create a poll", blocks=blocks, action_id="poll.create"),
        keep_view_id=True,
    )


@register_slack_action("poll.build.add_choice")
def poll_builder_add_choice(state):
    nb_choice = get_modal_metadata(state).get("nb_choice", 2) + 1
    blocks = get_blocks(nb_choice)

    update_modal(
        state,
        make_modal(
            state,
            title="Create a poll",
            blocks=blocks,
            action_id="poll.create",
            metadata={"nb_choice": nb_choice},
        ),
    )


@register_slack_action("poll.create")
def post_poll(state):
    if state.type == "block_actions":
        dispatch_modal_actions(state)
    elif state.type == "view_submission":
        modal_state = get_modal_state(state.payload)
        name = ""
        choices = []
        params = []
        for s in modal_state:
            if s.startswith("poll.choice"):
                if "value" in modal_state[s]:
                    choices.append(modal_state[s]["value"])
            if s == "poll.params":
                for options in modal_state[s].get("selected_options", []):
                    params.append(options["value"])
            if s == "poll.title":
                name = modal_state[s]["value"]

        create_poll(state, name, choices, params)
