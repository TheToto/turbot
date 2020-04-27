import logging

from django.http import HttpResponse

from workspaces.utils import SLACK_ACTIONS, SLACK_EVENTS, SLACK_COMMANDS
from .utils import SlackState

logger = logging.getLogger("slackbot")


def oauth(request):
    return "ok"


def action(request):
    state = SlackState.from_action_request(request)
    logger.debug(state)
    for action_fun in SLACK_ACTIONS[state.command]:
        action_fun(state)
    return HttpResponse(status=200)


def event(request):
    # payload = json.loads(request.body)
    # if payload["type"] == "url_verification":
    #    return JsonResponse({"challenge": payload["challenge"]})

    state = SlackState.from_event_request(request)
    logger.debug(state)
    event_name = state.command
    for event_fun in SLACK_EVENTS[event_name]:
        event_fun(state)
    return HttpResponse(status=200)


def command(request):
    logger.debug(request.body)
    state = SlackState.from_command_request(request)
    logger.debug(state)
    for command_fun in SLACK_COMMANDS[state.command]:
        command_fun(state)
    return HttpResponse(status=200)
