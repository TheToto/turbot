from django.apps import AppConfig


class WorkspacesConfig(AppConfig):
    name = "workspaces"

    def ready(self):
        from .actions import photo, report, spell_check, misc, modal
