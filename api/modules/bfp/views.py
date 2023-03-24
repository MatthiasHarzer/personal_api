from api.util.db_utils import get_store_item
from api.util.decorators import requires
from django.http import HttpResponse


@requires(permission="bfp-access-token")
def get_github_update_access_token(request):
    return HttpResponse(
            get_store_item("bfp-github-update-access-token")
        )
