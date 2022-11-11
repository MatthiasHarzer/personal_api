from django.urls import path

from api.modules.images import views

urlpatterns = \
    [

        path("genshin", views.get_genshin_image_by_tags)
    ]
