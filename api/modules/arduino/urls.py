# from django.conf.urls import url
from django.urls import path


from api.modules.arduino import views

urlpatterns = \
    [
        path("", views.home, name="home"),
        path("formattedtime", views.get_arduino_formatted_time),
        path("getclocksettings", views.get_arduino_clock_settings),
        path("setmultipleclocksettings", views.set_arduino_clock_settings),
        path("setclocksettings", views.set_single_arduino_clock_setting)
    ]
