from django.urls import path

from workspaces import views

urlpatterns = [
    # path("oauth", views.oauth, name="oauth"),
    path("action", views.action, name="action"),
    path("event", views.event, name="event"),
    path("command", views.command, name="command"),
]
