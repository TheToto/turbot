import json
from typing import Tuple, Optional
from dataclasses import dataclass
from functools import partial

from django.http import JsonResponse, HttpRequest
from django.conf import settings

from workspaces.models import Team, Channel, User
import logging

SLACK_ACTIONS = {}
SLACK_EVENTS = {}
SLACK_COMMANDS = {}

logger = logging.getLogger("slackbot")


def register_slack_action(name, **kwargs):
    print("Register action ", name)

    def __inner(f):
        f = partial(f, **kwargs)
        if name in SLACK_ACTIONS:
            SLACK_ACTIONS[name].append(f)
        else:
            SLACK_ACTIONS[name] = [f]
        return f

    return __inner


def register_slack_event(name, **kwargs):
    print("Register event ", name)

    def __inner(f):
        f = partial(f, **kwargs)
        if name in SLACK_EVENTS:
            SLACK_EVENTS[name].append(f)
        else:
            SLACK_EVENTS[name] = [f]

        return f

    return __inner


def register_slack_command(name, **kwargs):
    print("Register command ", name)

    def __inner(f):
        f = partial(f, **kwargs)
        if name in SLACK_COMMANDS:
            SLACK_COMMANDS[name].append(f)
        else:
            SLACK_COMMANDS[name] = [f]

        return f

    return __inner


def send_ephemeral(state, text, blocks=None, thread_ts=None):
    logger.debug(
        settings.SLACK_CLIENT.chat_postEphemeral(
            text=text,
            channel=state.channel.id,
            blocks=blocks,
            user=state.user.id,
            thread_ts=thread_ts if thread_ts else state.thread_ts,
        )
    )


def send_message(state, text, blocks=None, thread_ts=None):
    logger.debug(
        settings.SLACK_CLIENT.chat_postMessage(
            text=text,
            channel=state.channel.id,
            blocks=blocks,
            thread_ts=thread_ts if thread_ts else state.thread_ts,
        )
    )


class SlackErrorResponse(JsonResponse):
    def __init__(self, text: str, *args, **kwargs):
        super().__init__(
            {
                "response_type": "ephemeral",
                "text": text,
                "icon_url": settings.ERROR_ICON_URL,
            },
            *args,
            **kwargs
        )


def int_to_emoji(index: int):
    return [
        ":one:",
        ":two:",
        ":three:",
        ":four:",
        ":five:",
        ":six:",
        ":seven:",
        ":eight:",
        ":nine:",
    ][index]


@dataclass
class SlackState:
    team: Team
    user: User
    channel: Channel
    command: str  # if action, `action_id`
    text: str  # if action, `value`
    ts: Optional[str] = None
    thread_ts: Optional[str] = None
    trigger_id: Optional[str] = None
    response_url: Optional[str] = None

    @classmethod
    def from_command_request(cls, request: HttpRequest) -> "SlackState":
        team, _ = Team.objects.get_or_create(
            id=request.POST["team_id"], defaults={"domain": request.POST["team_domain"]}
        )

        channel, _ = Channel.objects.get_or_create(
            id=request.POST["channel_id"],
            team=team,
            defaults={"name": request.POST["channel_name"]},
        )

        user, _ = User.objects.get_or_create(
            id=request.POST["user_id"],
            team=team,
            defaults={"name": request.POST["user_name"]},
        )

        return cls(
            team,
            user,
            channel,
            command=request.POST["command"],
            text=request.POST["text"],
            trigger_id=request.POST["trigger_id"],
        )

    @classmethod
    def from_action_request(cls, request: HttpRequest) -> "SlackState":
        payload = json.loads(request.POST["payload"])

        team, _ = Team.objects.get_or_create(
            id=payload["team"]["id"], defaults={"domain": payload["team"]["domain"]}
        )

        channel, _ = Channel.objects.get_or_create(
            id=payload["channel"]["id"],
            team=team,
            defaults={"name": payload["channel"]["name"]},
        )

        user, _ = User.objects.get_or_create(
            id=payload["user"]["id"],
            team=team,
            defaults={"name": payload["user"]["name"]},
        )

        return cls(
            team,
            user,
            channel,
            command=payload["actions"][0]["action_id"],
            text=payload["actions"][0]["value"],
            trigger_id=payload["trigger_id"],
            response_url=payload["response_url"],
            ts=payload["message"]["ts"],
        )

    @classmethod
    def from_event_request(cls, request: HttpRequest) -> "SlackState":
        payload = json.loads(request.body)

        team = Team.objects.get(id=payload["event"]["team"])

        channel = Channel.objects.get(id=payload["event"]["channel"], team=team)

        user = User.objects.get(id=payload["event"]["user"], team=team)

        return cls(
            team,
            user,
            channel,
            command=payload["event"]["type"],
            text=payload["event"]["text"],
            thread_ts=payload["event"].get("thread_ts", None),
        )
