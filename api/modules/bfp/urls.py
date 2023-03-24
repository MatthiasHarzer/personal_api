# from django.conf.urls import url
from django.urls import path

from api.modules.bfp import views

urlpatterns = \
    [
        path("github-access-token", views.get_github_update_access_token),
    ]
