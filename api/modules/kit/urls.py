# from django.conf.urls import url
from django.urls import path

from api.modules.kit import views

urlpatterns = \
    [
        path("timetable", views.get_kit_timetable),
        path("timetableByUrl", views.get_kit_timetable_public),
    ]
