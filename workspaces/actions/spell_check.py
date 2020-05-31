import logging
from subprocess import check_output, STDOUT

from slackblocks import Text, SectionBlock
from turbot import settings
from workspaces.utils import register_slack_event, send_message, register_slack_action

logger = logging.getLogger("slackbot")


def launch_leodagan(input_str):
    result = check_output(
        ["python", "submodule/leodagan/leodagan.py", "-q"],
        stderr=STDOUT,
        input=input_str.encode(),
    )
    return result


def find_code_blocks(message):
    code_blocks_text = []
    if "blocks" in message:
        for block in message["blocks"]:
            for element in block["elements"]:
                if element["type"] == "rich_text_preformatted":  # Code block
                    current_text = ""
                    # Slack has the bad idea to split code blocks (for example for links)
                    for e in element["elements"]:
                        current_text += e["text"]
                    code_blocks_text.append(current_text)
    return code_blocks_text


def process_leodagan(state, message):
    texts_to_test = find_code_blocks(message)

    blocks = []
    for text in texts_to_test:
        leodagan_result = launch_leodagan(text).decode("utf-8")
        if not leodagan_result:
            leodagan_result = "La netiquette est conforme."
        blocks.append(SectionBlock(Text(f"```{leodagan_result}```")))

    if blocks:
        send_message(state, text="Léodagan report", blocks=repr(blocks))


@register_slack_action("leodagan.check")
def spell_check_shortcut(state):
    if state.thread_ts:
        query = settings.SLACK_CLIENT.conversations_replies(
            channel=state.channel.id,
            ts=state.ts,
            latest=state.thread_ts,
            limit=1,
            inclusive="true",
        )
    else:
        state.thread_ts = state.ts
        query = settings.SLACK_CLIENT.conversations_history(
            channel=state.channel.id, latest=state.ts, limit=1, inclusive="true",
        )
    message = query["messages"][0]
    process_leodagan(state, message)


@register_slack_event("app_mention")
def spell_check(state):
    if state.thread_ts:  # Mentioned in a thread
        query = settings.SLACK_CLIENT.conversations_history(
            channel=state.channel.id, latest=state.thread_ts, limit=1, inclusive="true",
        )
        message = query["messages"][0]
        process_leodagan(state, message)
