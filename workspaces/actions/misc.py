from ..utils import send_ephemeral, register_slack_command


@register_slack_command("/suffix")
def suffix(state):
    state.user.suffix = state.text
    state.user.save()
    send_ephemeral(state, f"Saved !\nNew display : {state.user.slack_username}")
