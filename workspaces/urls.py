from django.urls import path

from workspaces import views

urlpatterns = [
    path("oauth", views.oauth, name="oauth"),
    path("action", views.action, name="action"),
    path("test", views.test, name="test"),
    path("photo", views.photo, name="photo"),
    path("set-suffix", views.suffix, name="set-suffix"),
    path("report", views.report, name="report"),
]
