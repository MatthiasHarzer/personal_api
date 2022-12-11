# from django.conf.urls import url
from django.urls import path

from api.modules.request_catcher import views

urlpatterns = \
    [
        path("<slug:request_id>", views.catch_request),
        path("<slug:request_id>/view", views.view_requests)
    ]
