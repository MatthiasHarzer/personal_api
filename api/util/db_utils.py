import json
from typing import Callable, Union

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from api.models import StoreItem, WebsocketClients

Type_converter = Callable[[str], any]


def get_store_item(name: str, type_converter: Type_converter = None) -> any:
    """Get a store item from db with corresponding "name", and optionally convert it to new type (DB stores data as
    string) """
    try:
        item = StoreItem.objects.get(name=name)
    except StoreItem.DoesNotExist:
        # * If conversion error of StoreItem.DoesNotExist, return None
        return None

    value = item.value

    # * Check if data_type is set
    if type_converter is not None:
        value = type_converter(value)

    return value


def set_store_item(name: str, value: Union[str, int, float, dict, bool], update_scope_=True):
    """Set a store item with value to name in db, and optionally update the scope"""

    # * Try to get an existing item from db an update it
    try:
        item = StoreItem.objects.get(name=name)
        if type(value) == dict:
            item.value = json.dumps(value)
        else:
            item.value = str(value)
        item.save()

    # * or create a new one with value
    except StoreItem.DoesNotExist:
        item = StoreItem(name=name, value=value)
        item.save()

    if update_scope_:
        update_scope(name, value)


def update_scope(scope: str, data: Union[str, float, int, dict, list, set, tuple]):
    """Send update via channels to connect WS clients where <scope> is registered"""
    all_clients = WebsocketClients.objects.all()
    # print(scope, [(c.identifier, c.scopes) for c in all_clients])
    for client in all_clients:
        if scope not in client.scopes: continue

        channel_name = client.channel_name
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.send)(channel_name, {
            "type": "layer_receive",
            "rc_type": "update",
            "rc_scope": scope,
            "rc_data": data,
        })
