import json
import os
import re
from io import BytesIO

import requests
from PIL import Image
from django.http import HttpResponse, JsonResponse

from api.secrets import GOOGLE_MAPS_API_KEY
from api.util.decorators import requires, optional

HEX_COLOR_REGEX = re.compile(r'^#(?:[0-9a-fA-F]{3}){1,2}$')
PATH = os.path.dirname(os.path.realpath(__file__))
TEMPLATE_PATH = f"{PATH}/maps_style_template.json"


def get_map_style_with(roads_local, roads_arterial, roads_highway):
    replacements = [("color.road.arterial", roads_arterial), ("color.road.highway", roads_highway),
                    ("color.road.local", roads_local)]
    with open(TEMPLATE_PATH) as f:
        data = f.read()
        for r in replacements:
            color = f"#{r[1]}"

            if re.match(HEX_COLOR_REGEX, color) is None:
                raise Exception(f"Invalid color `{r[1]}`")
            data = data.replace(f"${r[0]}", color)
        style = json.loads(data)
        return style


def get_snapshot(url, cropped=False) -> BytesIO:
    image = Image.open(requests.get(url, stream=True).raw)

    height = image.height
    width = image.width

    if cropped:
        image = image.crop((0, 0, width, height - 40))

    output = BytesIO()
    image.save(output, "PNG")
    return output


@requires(permission="google-maps", query_params="center")
@optional(query_params=["cropped", "map_id", "zoom", "aspect_ratio"])
def make_maps_snapshot(request, center, cropped=None, map_id=None, zoom=None, aspect_ratio=None):
    """Make a snapshot of a map with the given parameters."""
    aspect_ratio = aspect_ratio if aspect_ratio is not None else "1:1"
    map_id = map_id if map_id is not None else "9394d5ca24cfc071"
    zoom = zoom if zoom is not None else 14
    cropped = False if cropped is None else cropped.lower() == "true"

    size = [640, 640]
    try:
        ar_w, ar_h = [int(r) for r in aspect_ratio.split(":")]
        if ar_w > ar_h:
            size[1] = size[1] * (ar_h / ar_w)
        else:
            size[0] = size[0] * (ar_w / ar_h)
    except Exception:
        pass

    _size = 'x'.join([str(int(s)) for s in size])

    url = f"https://maps.googleapis.com/maps/api/staticmap?key={GOOGLE_MAPS_API_KEY}&size={_size}&scale=2&center={center}&zoom={zoom}&format=png&maptype=roadmap&map_id={map_id}"

    output = get_snapshot(url, cropped)

    return HttpResponse(output.getvalue(), content_type="image/png")


@requires(permission="google-maps", query_params=["center", "roads_local", "roads_arterial", "roads_highway"])
@optional(query_params=["cropped", "zoom"])
def make_custom_maps_snapshot(request, center, roads_local, roads_arterial, roads_highway, cropped=None, zoom=None):
    """Make a snapshot of a map with the given parameters."""
    zoom = zoom if zoom is not None else 14
    cropped = False if cropped is None else cropped.lower() == "true"

    replacements = [("elementType", "element"), ("featureType", "feature"), ]
    try:
        json_style = get_map_style_with(roads_local, roads_arterial, roads_highway)
        styles = []

        for s in json_style:

            elements = []
            feature = s.get("featureType", None)
            element = s.get("elementType", None)
            stylers = s.get("stylers", [])
            if feature is not None:
                elements.append(f"feature:{feature}")
            if element is not None:
                elements.append(f"element:{element}")
            for styler in stylers:
                for k, v in styler.items():
                    elements.append(f"{k}:{str(v).replace('#', '0x')}")
            styles.append(f"style={'%7C'.join(elements)}")
        # print("&".join(styles))

        size = [640, 640]
        _size = 'x'.join([str(int(s)) for s in size])
        url = f"https://maps.googleapis.com/maps/api/staticmap?key={GOOGLE_MAPS_API_KEY}&size={_size}&scale=2&center={center}&zoom={zoom}&format=png&maptype=roadmap&{'&'.join(styles)}"
        output = get_snapshot(url, cropped)
        return HttpResponse(output.getvalue(), content_type="image/png")

    except Exception as e:
        return HttpResponse(
            json.dumps({"error": e, "message": "Color should be encoded as hex."}),
            content_type="application/json")


@requires(query_params=["roads_local", "roads_arterial", "roads_highway"])
def json_style_from_params(request, roads_local, roads_arterial, roads_highway):
    """Get the JSON style for the given parameters."""
    try:
        return JsonResponse(get_map_style_with(roads_local, roads_arterial, roads_highway), safe=False)
    except Exception as e:
        return HttpResponse(
            json.dumps({"error": e, "message": "Color should be encoded as hex."}),
            content_type="application/json")
