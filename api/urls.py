# from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include

from api.views import base_views
from personal_api import settings

urlpatterns = \
    [
        path("", include("api.modules.misc.urls")),
        path("", base_views.home, name="home"),
        path("kit/", include("api.modules.kit.urls")),
        path("arduino/", include("api.modules.arduino.urls"), name="arduino"),
        path("maps/", include("api.modules.maps.urls"), name="maps"),
        path("wgit/", include("api.modules.wgit.urls"), name="wgit"),
        path("images/", include("api.modules.images.urls"), name="images"),
        path("shortener/", include("api.modules.url_shortener.urls"), name="shortener"),
        path("catch/", include("api.modules.request_catcher.urls"), name="catcher"),
        path("test/wsupdatetest", base_views.ws_update_tester),
        path("bfp/", include("api.modules.bfp.urls"), name="bfp"),
    ] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
