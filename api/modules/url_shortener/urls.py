# from django.conf.urls import url
from django.urls import path

from api.modules.url_shortener import views

urlpatterns = \
    [
        path("set", views.create_or_edit_link),
        path("resolve/<str:short_id>", views.resolve_short_link_id),
    ]
