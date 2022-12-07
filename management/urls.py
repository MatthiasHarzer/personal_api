from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

urlpatterns = \
    [
        path("", views.home, name="Home"),
        path("create-new-permission", views.create_permission, name="create_new_permission"),
        path("keys/new", views.create_or_edit_key, name="New key"),
        path("keys/edit/<slug:key>/", views.create_or_edit_key, name="Edit key"),
        path("keys/delete/<slug:key>/", views.delete_key, name="delete key"),
        path("short_url/overview", views.short_url_overview, name="short_url_overview"),
        path("short_url/new", views.create_or_edit_short_url, name="New short url"),
        path("short_url/edit/<slug:short_id>/", views.create_or_edit_short_url,
             name="Edit short url"),
        path("store/new", views.create_or_edit_store_item, name="store item"),
        path("store/edit/<slug:item_key>/", views.create_or_edit_store_item,
             name="store item edit"),
        path("store/delete/<slug:item_key>/", views.delete_store_item,
             name="store item delete"),
        path("overview", views.get_overview, name="all keys"),
        # path("ws/getport", api_views.get_ws_port),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
