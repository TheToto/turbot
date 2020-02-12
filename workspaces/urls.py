from django.urls import path

from workspaces.views import misc, photo, report, spell_check

urlpatterns = [
    path("oauth", misc.oauth, name="oauth"),
    path("action", misc.action, name="action"),
    path("event", misc.event, name="event"),
    path("test", misc.test, name="test"),
    path("photo", photo.photo, name="photo"),
    path("set-suffix", misc.suffix, name="set-suffix"),
    path("report", report.report, name="report"),
]
