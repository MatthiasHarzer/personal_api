from django.http import JsonResponse

from api.services import firebase_service
from api.util.decorators import requires


@requires(permission="firebase", query_params="user_id")
def get_dynamic_link_for_user(request, user_id: str):
    """Creates a dynamic link for the given user_id and returns it."""

    link = firebase_service.create_dynamic_link_for_user(user_id)

    return JsonResponse({"link": link})


@requires(permission="firebase", query_params="link")
def get_user_id_by_dynamic_link(request, link: str):
    """Tries to fetch the user with the given dynLink from the firestore and returns its uid."""

    user_id = firebase_service.get_user_id_by_dynlink(link)

    return JsonResponse({"user_id": user_id})