from django.http import HttpResponse

from api.util.db_utils import update_scope
from api.util.decorators import requires


def home(request):
    return HttpResponse("You are home")


@requires(query_params=["scope"])
def ws_update_tester(request, scope):
    data = {
        "WS_TEST": "UPDATED",
        "value": 564
    }
    # n, ln = WebsocketServer.update(scope, data)

    update_scope(scope, data)

    # WebsocketServer.send_to("ws_test", {"data": "abc"}, ws_test_cb)

    return HttpResponse(f"Updated")
