import logging
import re

import slack.errors
from django.db import transaction
from django.http import HttpResponse

from polls.models import Poll, Choice, UserChoice
from workspaces.models import User
from workspaces.utils import (
    SlackErrorResponse,
    get_request_entities,
    register_slack_action,
)
from django.conf import settings

logger = logging.getLogger("slackbot")

POLL_TEXT_PATTERN = re.compile(
    "\s*(?P<start_quote>[‘’“”'\"])(((?!(?P=start_quote)).)+)(?P=start_quote)\s*"
)


class InvalidPollException(BaseException):
    pass


def get_poll_choices(text) -> (str, [str]):
    values = [value[1] for value in POLL_TEXT_PATTERN.findall(text)]

    if len(values) < 3:
        raise InvalidPollException("You must provide a name and at least two choices")
    elif len(values) > 10:
        raise InvalidPollException("You cannot have more than 9 choices")

    return values[0], values[1:]


@transaction.atomic
@register_slack_action("polls.vote")
def vote(payload):
    user, _ = User.objects.get_or_create(
        id=payload["user"]["id"],
        team_id=payload["user"]["team_id"],
        defaults={"name": payload["user"]["username"]},
    )

    choice = Choice.objects.prefetch_related("voters", "poll").get(
        id=payload["actions"][0]["value"]
    )

    if choice.voters.filter(id=user.id).exists():
        choice.voters.remove(user)
    else:
        if choice.poll.unique_choice:
            UserChoice.objects.filter(
                user__id=user.id, choice__poll=choice.poll
            ).delete()
        choice.voters.add(user)

    logger.debug(
        settings.SLACK_CLIENT.chat_update(
            ts=payload["message"]["ts"],
            text=f"Poll: {choice.poll.name}",
            channel=payload["channel"]["id"],
            blocks=choice.poll.slack_blocks,
        )
    )

    return HttpResponse(status=200)


@transaction.atomic
@register_slack_action("polls.delete")
def delete(payload):
    user = User.objects.get(id=payload["user"]["id"])
    poll = Poll.objects.get(id=payload["actions"][0]["value"])

    if not user.has_permissions and user != poll.creator:
        logger.debug(
            settings.SLACK_CLIENT.chat_postMessage(
                text=f"I'm sorry {user.slack_username}, I'm afraid I can't do that...",
                channel=poll.channel.id,
            )
        )
        return HttpResponse(status=200)

    logger.debug(
        settings.SLACK_CLIENT.chat_delete(
            ts=payload["message"]["ts"], channel=poll.channel.id,
        )
    )

    logger.debug(
        settings.SLACK_CLIENT.chat_postMessage(
            text=f"A poll was deleted by {user.slack_username}",
            channel=poll.channel.id,
        )
    )

    poll.delete()
    return HttpResponse(status=200)


@transaction.atomic
def create(request, unique=False, anonymous=False):
    try:
        name, choices = get_poll_choices(request.POST["text"])
    except InvalidPollException as e:
        return SlackErrorResponse(
            f":x: {e} :x:\n`{request.POST['command']} {request.POST['text']}`"
        )

    team, channel, creator = get_request_entities(request)

    poll = Poll.objects.create(
        name=name,
        creator=creator,
        channel=channel,
        unique_choice=unique,
        anonymous=anonymous,
        visible_results=not anonymous,
    )

    for index, choice in enumerate(choices):
        poll.choices.create(index=index, text=choice)

    try:
        settings.SLACK_CLIENT.chat_postMessage(
            channel=channel.id, text=f"Poll: {poll.name}", blocks=poll.slack_blocks,
        )
    except slack.errors.SlackApiError:
        return SlackErrorResponse(
            f":x: Could not create the poll. Is <@{settings.TURBOT_USER_ID}> in the channel ? :x:\n`{request.POST['command']} {request.POST['text']}`"
        )

    return HttpResponse(status=200)


@transaction.atomic
@register_slack_action("polls.reveal")
def reveal_results(payload):
    user = User.objects.get(id=payload["user"]["id"])
    poll = Poll.objects.get(id=payload["actions"][0]["value"])

    if poll.creator.id != user.id:
        return SlackErrorResponse(f"You are not the creator of this poll.")

    poll.visible_results = True
    poll.save()

    settings.SLACK_CLIENT.chat_update(
        ts=payload["message"]["ts"],
        text=f"Poll: {poll.name}",
        channel=payload["channel"]["id"],
        blocks=poll.slack_blocks,
    )

    return HttpResponse(status=200)
