import json
import logging

from django.http import HttpResponse, JsonResponse

from workspaces.utils import SLACK_ACTIONS, get_request_entities, SLACK_EVENTS

logger = logging.getLogger("slackbot")


def oauth(request):
    return "ok"


def test(request):
    return "ok"


def suffix(request):
    _, _, user = get_request_entities(request)
    user.suffix = request.POST["text"]
    user.save()
    return JsonResponse({"text": f"Saved !\nNew display : {user.slack_username}"})


def action(request):
    payload = json.loads(request.POST["payload"])
    logger.debug(payload)
    action_name: str = payload["actions"][0]["action_id"]
    return SLACK_ACTIONS[action_name](payload)


def event(request):
    payload = json.loads(request.body)
    logger.debug(payload)
    if payload["type"] == "url_verification":
        return JsonResponse({"challenge": payload["challenge"]})
    if payload["type"] == "event_callback":
        event_name = payload["event"]["type"]
        return SLACK_EVENTS[event_name](payload)
    return HttpResponse(status=200)
