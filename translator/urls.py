from django.urls import path
from . import views

app_name = "translator"

urlpatterns = [
    path("", views.landing, name="landing"),
    path("landing.html", views.landing, name="landing_legacy"),
    path("lading.html", views.landing, name="lading_legacy"),
    path("main/", views.dashboard, name="dashboard"),
    path("main", views.dashboard, name="dashboard_legacy"),
    path("history/", views.history, name="history"),
    path("languages/", views.languages, name="languages"),
    path("languages", views.languages, name="languages_legacy"),
    path("speak/", views.speak, name="speak"),
    path("speak", views.speak, name="speak_legacy"),
]
