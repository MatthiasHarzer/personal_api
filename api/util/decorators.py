"""
Decorator for required permission and/or params for view (query_params returned as kwarg)
"""
from typing import Union

from api.models import ApiKey, Permission
from api.util import tc
from api.util.utils import error

TypedParam = tuple[str, tc.TypeConverter]


def requires(permission: Union[list[str], str] = None, query_params: Union[list[str], str] = None):
    """Requires a permission and/or query_params for the view"""

    # * Make params set
    query_params: set = set([]) if query_params is None else set(
        query_params if type(query_params) == list else [query_params])
    permission: set = set([]) if permission is None else set(permission if type(permission) == list else [permission])

    def decorator(func):
        def wrapper(*args, **kwargs):
            # * The first arg should be the request
            request = args[0]

            # * URL Params
            request_params = request.GET
            # print(request_params)

            # * If permission are required, check
            if len(permission) > 0:

                # * Get the key-object from the url; If no key -> error
                try:
                    key = ApiKey.objects.get(value=request_params.get("key", ""))
                except ApiKey.DoesNotExist:
                    return error(401, "Unauthorized")

                # * Get keys permission
                key_permission = set([p.name for p in Permission.objects.filter(apikey=key)])

                # print("KP:", key_permission)

                # * Check if query-key has the required permission
                if not permission.issubset(key_permission):
                    return error(401, "Unauthorized")

            # * Check for required params
            missing_qparams: list[str] = []
            for query_param in query_params:
                p = request_params.get(query_param, None)
                # print(query_param, p)
                # * if p is none, the param wasn't found in the url -> add it to missing-list
                if p is None:
                    missing_qparams.append(query_param)
                # * else set it as kwarg
                else:
                    kwargs[query_param] = p
            # * if one or more items in missing_qparams, return error page with missing info
            if len(missing_qparams) > 0:
                return error(400, {"missing": missing_qparams})
            # * else run the function with new kwargs
            else:
                return func(*args, **kwargs)

        return wrapper

    return decorator


def optional(query_params: Union[list[Union[str, TypedParam]], str, TypedParam], prefix: str = "", suffix: str = ""):
    """Optional query_params for the view. If the param is found, it will be returned as kwarg with prefix/suffix"""

    # * Query params as set
    query_params: set = set(query_params if type(query_params) == list else [query_params])

    query_params_with_type: set[tuple[str, tc.TypeConverter]] = set()
    for param in query_params:
        if type(param) == tuple:
            query_params_with_type.add(param)
        else:
            query_params_with_type.add((param, str))

    def decorator(func):
        def wrapper(*args, **kwargs):
            # * The first arg should be the request
            request = args[0]

            # * URL Params
            request_params = request.GET

            # * Check URL-params for query_params
            for param, _type in query_params_with_type:
                # * Get the param from the URL-params or None and set kwarg (can be None, cause optional)
                value = request_params.get(param, None)
                kwargs[f"{prefix}{param}{suffix}"] = value if value is None else _type(value)

            # * Call the function with modified kwargs
            return func(*args, **kwargs)

        return wrapper

    return decorator
