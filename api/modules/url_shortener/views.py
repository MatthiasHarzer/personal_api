from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt

from api.models import URLShortener
from api.services import url_shortener
from api.util import utils
from api.util.decorators import requires, optional


@requires(permission="url_shortener")
def create_or_edit_link(request):
    """Generates a short link id for the given url"""

    if request.method == "POST":
        url = request.POST.get("url")
        short_id = request.POST.get("short_id")

        if not url:
            return utils.error(400, "Bad Request")
        return HttpResponse(url_shortener.create_or_edit(url, short_id))

    return utils.error(400, "Bad Request")


def resolve_short_link_id(request, short_id):
    """Resolves a short link id to the original url"""

    link = url_shortener.resolve(short_id)
    if link:
        return redirect(link)
    return utils.error(404, "Not Found")

