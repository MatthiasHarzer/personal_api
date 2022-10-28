# ! Used for WS connection
import json
from typing import Union

from channels.generic.websocket import WebsocketConsumer

# from api.views.base_views import consumer_ws_callback_handler
from api.models import WebsocketClients, StoreItem
from api.util.utils import random_string, dict_to_b64, b64_to_dict

"""Data structure:

data = {
    # ident and meta stuff
    meta: {
        type: "...",
        id: "...",
        ...  
    },
    # Data to send/receive
    data: {
        
    }
}

"""

# * Clear WS Clients on server startup
WebsocketClients.objects.all().delete()


class WebsocketServer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)

        # * Each client should have a unique identifier
        self.identifier = None
        # * Each client has subscribed scopes (on scope-change -> callback)
        self.scopes: list[str] = []

        self.receive_callbacks: list[tuple[str, str]] = []
        print(f"New client connected: {self}")

    def __str__(self):
        return f"WSClient: id: {self.identifier}"

    # ! register a scope to sub to for current client; when scope updates -> send update to client
    def register_scopes(self, scopes):
        print(f"Registering {scopes = } for {self}")
        # * add scopes to self.scopes if they weren't registered before
        for s in scopes:
            if s not in self.scopes:
                self.scopes.append(s)

            # * Try to send the value of the scope to the client if it is in StoreItem DB
            try:
                item = StoreItem.objects.get(name=s)
                v = item.value

                # * Try to convert the item value into correct format and send it to client on registration
                try:
                    v = json.loads(v)
                except Exception:
                    try:
                        v = float(v)
                    except Exception:
                        try:
                            v = int(v)
                        except Exception:
                            pass

                self.send(dict_to_b64(self.message_builder(v, {"type": "callback", "scope": s})))
            except Exception as e:
                print(e)

        # * Update DB WS Client entry with current scopes (i think it's redundant but ok)
        c = WebsocketClients.objects.get(channel_name=self.channel_name)
        c.scopes = self.scopes
        c.save()

    # ! unregister scope(s) -> don't receive updates on scope change
    def unregister_scopes(self, scopes):
        print(f"Unregistering {scopes = } for {self}")
        # * delete scope (or all) if there are any
        if scopes == "all":
            self.scopes = []
        else:
            for s in scopes:
                if s in self.scopes:
                    self.scopes.remove(s)

            c = WebsocketClients.objects.get(channel_name=self.channel_name)
            c.scopes = self.scopes
            c.save()

    # ! Called on client connect
    def connect(self):
        # * Make new DB entry with channel name (so the views can access channels-layer to communicate with client)
        WebsocketClients.objects.create(channel_name=self.channel_name)
        self.accept()

    # ! Called on client disconnect
    def disconnect(self, close_code):
        # * Delete client from DB
        WebsocketClients.objects.filter(channel_name=self.channel_name).delete()

    # ! Called on client receive message
    def receive(self, text_data=None, bytes_data=None):
        try:
            # * Decode the message
            text_data_json = b64_to_dict(text_data) or json.loads(text_data)  # * Data the client sent

            print(f"{self} RECEIVED", text_data_json)

            # * Get meta data from message
            meta = text_data_json.get("meta", {})  # * Data for good communication (ex. rc_id, etc)

            # * Get message type
            type_ = meta.get("type", None)

            # print(meta)

            if type_ == "register":
                # * Register scopes
                self.register_scopes(meta.get("scopes", []))
            elif type_ == "unregister":
                # * Unregister scopes
                self.unregister_scopes(meta.get("scopes", []))
            elif type_ == "identifier":
                # * set identifier
                self.identifier = meta.get("id", "")

                # * Update DB entry with identifier
                c = WebsocketClients.objects.get(channel_name=self.channel_name)
                c.identifier = self.identifier
                c.save()
            elif type_ == "response":
                # * Check for response callback listeners
                self.__receive_callback_checker(text_data_json)
        except Exception:
            self.send("Error")

    # ! Registers callbacks with a generated id and returns it
    def __set_receive_callback(self, callback_id) -> str:
        sid = random_string(50)
        self.receive_callbacks.append((sid, callback_id))
        # print(self.receive_callbacks)
        return sid

    def __receive_callback_checker(self, text_data_json: dict):
        meta = text_data_json.get("meta", {})
        data = text_data_json.get("data", {})
        receive_id: str = meta.get("sid", "")

        index = 0
        for sid, callback_id in self.receive_callbacks:
            if sid == receive_id:
                # consumer_ws_callback_handler(callback_id, data)
                self.receive_callbacks.pop(index)
                break
            index += 1

    def layer_receive(self, event: dict):

        print(event)

        rc_data = event.get("rc_data", {})
        type_ = event.get("rc_type", None)

        if type_ == "send":
            send_data: Union[dict, str] = rc_data.get("data", {})

            # print(send_data)

            send_type: str = rc_data.get("type", "")

            callback_id = rc_data.get("callback_id", None)

            if type(send_data) == str:
                self.send(send_data)
            else:
                to_send = WebsocketServer.message_builder(send_data, {"type": send_type})
                # print(callback_id)
                if callback_id is not None:
                    sid = self.__set_receive_callback(callback_id)
                    to_send["meta"]["sid"] = sid
                    # print(sid)
                print("SENDING:", to_send)
                self.send(dict_to_b64(to_send))
        elif type_ == "update":
            rc_scope = event.get("rc_scope", "")
            self.send(dict_to_b64(WebsocketServer.message_builder(rc_data, {"type": "callback", "scope": rc_scope})))

    @staticmethod
    def message_builder(data: dict = None, meta: dict = None):
        data = {} if data is None else data
        meta = {} if meta is None else meta

        return {"data": data, "meta": meta}

    """
    @staticmethod
    def send_to(identifier: str, data: Union[dict, str], type_: str = None, callback: callable = None):
        for client in WebsocketServer.clients:
            if client.identifier == identifier:

                if type(data) == str:
                    client.send(data)
                else:
                    to_send = WebsocketServer.message_builder(data, {"type": type_ if type_ is not None else ""})
                    if callback:
                        id_ = client.__set_receive_callback(callback)
                        to_send["meta"]["sid"] = id_
                    client.send(to_b64(to_send))

    @staticmethod
    def update(scope: str, data: dict):
        # * Check which clients has registered the given scope and send data to them
        i = 0
        for client in WebsocketServer.clients:
            if scope in client.scopes:
                i += 1
                client.send(to_b64(WebsocketServer.message_builder(data, {"type": "callback", "scope": scope})))
        return i, len(WebsocketServer.clients)
    """
