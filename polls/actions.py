import logging
import re

import slack.errors
from django.conf import settings
from django.db import transaction

from slackblocks import (
    InputBlock,
    TextInput,
    make_modal,
)
from polls.models import Poll, Choice, UserChoice
from workspaces.utils import (
    register_slack_action,
    register_slack_command,
    send_message,
    send_ephemeral,
)
from workspaces.actions.modal import send_modal, get_modal_state


logger = logging.getLogger("slackbot")

POLL_TEXT_PATTERN = re.compile(
    "\s*(?P<start_quote>[‘’“”'\"])(((?!(?P=start_quote)).)+)(?P=start_quote)\s*"
)


class InvalidPollException(BaseException):
    pass


def get_poll_choices(text, is_open=False) -> (str, [str]):
    values = [value[1] for value in POLL_TEXT_PATTERN.findall(text)]

    if len(values) < 3 and not is_open:
        raise InvalidPollException("You must provide a name and at least two choices")

    return values[0], values[1:]


@transaction.atomic
@register_slack_action("polls.vote")
def vote(state):
    choice = Choice.objects.prefetch_related("voters", "poll").get(id=state.text)

    if choice.voters.filter(id=state.user.id).exists():
        choice.voters.remove(state.user)
    else:
        if choice.poll.unique_choice:
            UserChoice.objects.filter(
                user__id=state.user.id, choice__poll=choice.poll
            ).delete()
        choice.voters.add(state.user)

    logger.debug(
        settings.SLACK_CLIENT.chat_update(
            ts=state.ts,
            text=f"Poll: {choice.poll.name}",
            channel=state.channel.id,
            blocks=choice.poll.slack_blocks,
        )
    )


@transaction.atomic
@register_slack_action("polls.delete")
def delete(state):
    poll = Poll.objects.get(id=state.text)

    if not state.user.has_permissions and state.user != poll.creator:
        send_ephemeral(state, f"You are not the creator of this poll.")

    logger.debug(
        settings.SLACK_CLIENT.chat_delete(ts=state.ts, channel=poll.channel.id,)
    )

    send_message(state, f"A poll was deleted by {state.user.slack_username}")
    poll.delete()


@register_slack_command("/poll", params=[])
@register_slack_command("/poll-open", params=["open"])
@register_slack_command("/poll-unique", params=["unique"])
@register_slack_command("/poll-anon", params=["annon"])
@register_slack_command("/poll-anon-unique", params=["unique", "annon"])
@transaction.atomic
def create(state, params=[]):
    try:
        name, choices = get_poll_choices(state.text, "open" in params)
    except InvalidPollException as e:
        return send_ephemeral(state, f":x: {e} :x:\n`/poll {state.text}`")

    poll = Poll.objects.create(
        name=name,
        creator=state.user,
        channel=state.channel,
        unique_choice="unique" in params,
        anonymous="annon" in params,
        visible_results="annon" not in params,
        open_choice="open" in params,
    )

    for index, choice in enumerate(choices):
        poll.choices.create(index=index, text=choice)

    try:
        send_message(state, text=f"Poll: {poll.name}", blocks=poll.slack_blocks)
    except slack.errors.SlackApiError as e:
        logger.error(e)
        poll.delete()
        return send_ephemeral(
            state,
            f":x: Could not create the poll. Is <@{settings.TURBOT_USER_ID}> in the channel ? :x:\n`/poll {state.text}`",
        )


@transaction.atomic
@register_slack_action("polls.reveal")
def reveal_results(state):
    poll = Poll.objects.get(id=state.text)

    if poll.creator.id != state.user.id:
        send_ephemeral(state, f"You are not the creator of this poll.")

    poll.visible_results = True
    poll.save()

    settings.SLACK_CLIENT.chat_update(
        ts=state.ts,
        text=f"Poll: {poll.name}",
        channel=state.channel.id,
        blocks=poll.slack_blocks,
    )


@register_slack_action("polls.new_choice")
def modal_new_choice(state):
    blocks = [
        InputBlock("New choice", element=TextInput("polls.choice")),
    ]

    send_modal(
        state,
        make_modal(
            state,
            title="Submit a new choice",
            blocks=blocks,
            action_id="polls.new_choice.send",
            value=state.text,
        ),
    )


@transaction.atomic
@register_slack_action("polls.new_choice.send")
def add_new_choice(state):
    if state.type == "view_submission":
        modal_state = get_modal_state(state.payload)
        choice = modal_state["polls.choice"]["value"]

        poll = Poll.objects.get(id=state.text)

        poll.choices.create(index=len(poll.choices.all()), text=choice)

        settings.SLACK_CLIENT.chat_update(
            ts=state.ts,
            text=f"Poll: {poll.name}",
            channel=state.channel.id,
            blocks=poll.slack_blocks,
        )
