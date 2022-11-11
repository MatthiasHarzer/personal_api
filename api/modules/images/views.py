from django.http import JsonResponse

from api.util import tc
from api.util.decorators import requires, optional


@optional(query_params=("tags", tc.str_to_list))
def get_genshin_image_by_tags(_, tags: list[str]):
    return JsonResponse({
        "data": tags
    })
