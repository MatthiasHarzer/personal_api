from django.urls import path

from api.modules.maps import views

urlpatterns = \
    [

        path("snapshot", views.make_maps_snapshot),
        path("customsnapshot", views.make_custom_maps_snapshot),
        path("jsonstyle", views.json_style_from_params),
    ]
