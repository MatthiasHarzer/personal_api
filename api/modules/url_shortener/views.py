from django.http import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt

from api.models import URLShortener
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
        # print(url, short_id, short_id is None)

        if short_id is None:
            existing_ids = [o.short_id for o in URLShortener.objects.all()]
            short_id = utils.random_string(5)
            while short_id in existing_ids:
                short_id = utils.random_string(5)

        if not URLShortener.objects.filter(short_id=short_id).exists():
            URLShortener(short_id=short_id, url=url).save()
        else:
            URLShortener.objects.filter(short_id=short_id).update(url=url)

        return HttpResponse(short_id)

    return utils.error(400, "Bad Request")


def resolve_short_link_id(request, short_id):
    """Resolves a short link id to the original url"""

    try:
        short = URLShortener.objects.get(short_id=short_id)
        return redirect(short.url)
    except URLShortener.DoesNotExist:
        return utils.error(404, "Not Found")
