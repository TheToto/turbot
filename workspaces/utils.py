import json
import logging
from dataclasses import dataclass
from functools import partial
from typing import Optional

from django.conf import settings
from django.http import JsonResponse, HttpRequest

from workspaces.models import Team, Channel, User

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


def int_to_emoji(index: int):
    emoji_list = [
        ":zero:",
        ":one:",
        ":two:",
        ":three:",
        ":four:",
        ":five:",
        ":six:",
        ":seven:",
        ":eight:",
        ":nine:",
    ]
    digits = [int(x) for x in str(index + 1)]
    return "".join(map(lambda x: emoji_list[x], digits))


@dataclass
class SlackState:
    team: Team
    user: User
    channel: Channel
    type: str
    command: str  # if block_actions, `action_id`
    text: str  # if block_actions, `value`
    payload: dict
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
            type="command",
            command=request.POST["command"],
            text=request.POST["text"],
            payload=request.POST,
            trigger_id=request.POST["trigger_id"],
        )

    @classmethod
    def from_action_view_request(cls, request: HttpRequest) -> "SlackState":
        payload = json.loads(request.POST["payload"])

        private_metadata = json.loads(payload["view"]["private_metadata"])

        team = Team.objects.get(id=payload["team"]["id"])

        channel = Channel.objects.get(id=private_metadata.get("channel_id"), team=team)

        user = User.objects.get(id=payload["user"]["id"], team=team)

        return cls(
            team,
            user,
            channel,
            type=payload["type"],
            command=private_metadata.get("action_id"),
            text=private_metadata.get("value"),
            payload=payload,
            ts=private_metadata.get("ts"),
            thread_ts=private_metadata.get("thread_ts"),
            trigger_id=payload["trigger_id"],
        )

    @classmethod
    def from_action_request(cls, request: HttpRequest) -> "SlackState":
        payload = json.loads(request.POST["payload"])

        if "view" in payload:
            return cls.from_action_view_request(request)

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

        command = payload["actions"][0]["action_id"] if "actions" in payload else payload["callback_id"]
        text = payload["actions"][0]["value"] if "actions" in payload else ""

        return cls(
            team,
            user,
            channel,
            type=payload["type"],
            command=command,
            text=text,
            payload=payload,
            trigger_id=payload["trigger_id"],
            response_url=payload["response_url"],
            ts=payload.get("container", {}).get("message_ts", payload.get("message", {}).get("ts")),
            thread_ts=payload.get("message", {}).get("thread_ts"),
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
            type=payload["type"],
            command=payload["event"]["type"],
            text=payload["event"]["text"],
            payload=payload,
            thread_ts=payload["event"].get("thread_ts", None),
        )
