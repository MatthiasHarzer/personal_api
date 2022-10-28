from django.urls import path

from api.modules.wgit import views

urlpatterns = \
    [
        path("getdynamiclink", views.get_dynamic_link_for_user),
        path("getuserbydynlink", views.get_user_id_by_dynamic_link),
    ]
