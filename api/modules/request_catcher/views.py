from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from api.models import RequestCatcherItem
from api.util import utils
from api.util.decorators import requires
from api.util.utils import error


def catch_request(request, request_id):
    """Catch a request and return it as a json response"""

    relevant_headers = ["Host", "User-Agent", "Sec-Ch-Ua-Platform", "Accept-Language"]

    catch = RequestCatcherItem(
        request_id=request_id,
        ip_address=request.META.get("REMOTE_ADDR"),
        request_method=request.method,
        request_headers={k: v for k, v in request.headers.items() if k in relevant_headers},
        request_body=request.body.decode("utf-8"),
        content_type=request.content_type,
    )
    catch.save()

    return JsonResponse(catch.as_json())


@requires(superuser=True)
def view_requests(request, request_id):
    """View a request by id"""

    try:
        catches = RequestCatcherItem.objects.filter(request_id=request_id)
    except RequestCatcherItem.DoesNotExist:
        return error(404, "Not Found")

    context = {
        "request_id": request_id,
        "catches": catches,
    }

    return render(request, "api/view_requests.html", context)


@requires(superuser=True)
@csrf_exempt
def delete_request(request, request_id):
    """Delete a request by id"""

    try:
        catches = RequestCatcherItem.objects.filter(request_id=request_id)
    except RequestCatcherItem.DoesNotExist:
        return error(404, "Not Found")

    catches.delete()

    return utils.success()
