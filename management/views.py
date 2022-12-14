import random
import string

from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest
from django.shortcuts import render

from api.models import *
from api.services import url_shortener
from api.util.decorators import requires
from .forms import *


# Create your views here.


def home(request):
    # print(request.user.is_superuser)
    # print(get_resolver().url_patterns)
    return HttpResponseRedirect("/manage/overview")


def create_permission(request):
    if not request.user.is_superuser:  # Only su can create new permission/key/etc...
        return HttpResponse("Insufficient permission")

    context = {}

    if request.method == "POST":
        form = PermissionForm(request.POST)

        if form.is_valid():
            permission_name = form.cleaned_data.get("name")

            new_permission = Permission(name=permission_name)
            new_permission.save()
    else:
        form = PermissionForm()

    context["form"] = form
    context["site"] = "permission"

    return render(request, "management/permission.html", context)


def create_or_edit_key(request, key=None):
    if not request.user.is_superuser:  # Only su can create new permission/key/etc...
        return HttpResponse("Insufficient permission")

    current_permission = None
    name = ""
    context = {}

    if key:
        try:
            k = ApiKey.objects.get(value=key)
            current_permission = k.permission.all()
            name = k.name
        except (KeyError, ApiKey.DoesNotExist):
            return HttpResponseRedirect(f"/manage/key/new")

    if request.method == "POST":  # FORM submit
        form = ApiKeyForm(request.POST, permission=Permission.objects.all(), current_permission=current_permission,
                          edit=key is not None, name=name)

        if form.is_valid():
            permission = form.cleaned_data.get("permission")
            length = form.cleaned_data.get("length")
            name = form.cleaned_data.get("name")

            if key:
                try:
                    k = ApiKey.objects.get(value=key)
                    k.permission.clear()
                    for p in permission:
                        k.permission.add(p)
                    k.name = name
                    k.save()
                except ApiKey.DoesNotExist:
                    return HttpResponseRedirect(f"/manage/key/new")

            else:
                while True:
                    key = random_string(max(min(200, length), 10))
                    try:
                        ApiKey.objects.get(value=key)
                    except (KeyError, ApiKey.DoesNotExist):
                        new_key = ApiKey(value=key, name=name)
                        new_key.save()

                        for p in permission:
                            new_key.permission.add(p)

                        new_key.save()

                        return HttpResponseRedirect(f"/manage/keys/edit/{key}/")
    else:
        # print(current_permission)
        form = ApiKeyForm(permission=Permission.objects.all(), current_permission=current_permission,
                          edit=key is not None, name=name)

    context["form"] = form
    context["edit"] = key is not None
    context["key"] = key
    context["site"] = "new"
    # print(context)
    return render(request, "management/key.html", context)


def get_overview(request):
    if not request.user.is_superuser:  # Only su can create new permission/key/etc...
        return HttpResponse("Insufficient permission")
    store_items = [{"name": si.name, "value": si.value, "confidential": si.confidential} for si in
                   StoreItem.objects.all()]
    keys = ApiKey.objects.all()
    all_permission = [p.name for p in Permission.objects.all()]
    context = {
        "keys": [
            {"name": key.name, "value": key.value, "permission": ", ".join([p.name for p in key.permission.all()])}
            for key in
            keys], "site": "all", "all_permission": all_permission, "store_items": store_items}

    return render(request, "management/overview.html", context)


def delete_key(request, key=None):
    if not request.user.is_superuser:  # Only su can create new permission/key/etc...
        return HttpResponse("Insufficient permission")
    try:
        ApiKey.objects.get(value=key).delete()
    except (KeyError, ApiKey.DoesNotExist):
        pass
    return HttpResponseRedirect("/manage/overview")


def create_or_edit_store_item(request, item_key=None):
    if not request.user.is_superuser:  # Only su can create new permission/key/etc...
        return HttpResponse("Insufficient permission")

    item_value = None
    confidential = False
    context = {}

    if item_key:
        try:
            k = StoreItem.objects.get(name=item_key)
            item_value = k.value
            confidential = k.confidential
        except (KeyError, StoreItem.DoesNotExist):
            return HttpResponseRedirect(f"/manage/store/new")

    if request.method == "POST":  # FORM submit
        form = StoreItemForm(item_key, item_value, confidential, request.POST)

        if form.is_valid():
            name = form.cleaned_data.get("name")
            value = form.cleaned_data.get("value")
            confidential = form.cleaned_data.get("confidential")

            try:
                store_item = StoreItem.objects.get(name=name)
                store_item.value = value
                store_item.confidential = confidential
                store_item.save()
            except StoreItem.DoesNotExist:
                store_item = StoreItem(name=name, value=value, confidential=confidential)
                store_item.save()

    form = StoreItemForm(name=item_key, value=item_value, confidential=confidential)

    context["form"] = form
    context["edit"] = item_key is not None
    context["item_key"] = item_key
    context["site"] = "store_new"

    return render(request, "management/store.html", context)


def short_url_overview(request):
    if not request.user.is_superuser:  # Only su
        return HttpResponse("Insufficient permission")
    try:
        base_url = StoreItem.objects.get(name="url_shortener_base_url").value
    except StoreItem.DoesNotExist:
        base_url = "https://s.taptwice.dev/"

    context = {
        "base_url": base_url,
        "site": "short_url",
        "short_urls": [su for su in URLShortener.objects.all()]
    }

    return render(request, "management/short_url_manager.html", context)


def delete_short_url(request, short_id):
    if not request.user.is_superuser:  # Only
        return HttpResponse("Insufficient permission")

    try:
        URLShortener.objects.get(short_id=short_id).delete()
    except (KeyError, URLShortener.DoesNotExist):
        pass
    return HttpResponseRedirect("/manage/short_url/overview")


def create_or_edit_short_url(request, short_id=None):
    if not request.user.is_superuser:  # Only su can create new permission/key/etc...
        return HttpResponse("Insufficient permission")

    context = {}
    url = url_shortener.resolve(short_id)

    if request.method == "POST":
        form = UrlShortenerForm(request.POST)
        if not form.is_valid():
            return HttpResponse("Invalid form")

        if short_id is None:
            short_id = form.cleaned_data.get("short_id")
        if len(short_id) <= 0:
            short_id = None
        url = form.cleaned_data.get("url")
        short_id = url_shortener.create_or_edit(url, short_id)

    edit = short_id is not None
    form = UrlShortenerForm(short_id=short_id, url=url, edit=edit)

    context["form"] = form
    context["edit"] = edit
    context["short_id"] = short_id
    context["site"] = "short_url"

    return render(request, "management/short_url.html", context)


@requires(superuser=True)
def upload_or_edit_image(request):
    """
    Upload or edit an image
    :param request:
    :return:
    """
    if request.method == "POST":
        form = UploadOrEditImageForm(request.POST, request.FILES)
        if not form.is_valid():
            return HttpResponseBadRequest("Invalid form")

        image = form.cleaned_data.get("image")
        name = form.cleaned_data.get("name")
        tags = form.cleaned_data.get("tags")
        try:
            image = Image.objects.get(name=name, tags=tags)
            image.image = image
            image.save()
        except Image.DoesNotExist:
            image = Image(name=name, image=image, tags=tags)
            image.save()
        return HttpResponseRedirect("/manage/images/")
    else:
        form = UploadOrEditImageForm()

    return render(request, "management/image.html", {"form": form})


def delete_store_item(request, item_key):
    if not request.user.is_superuser:  # Only su can create new permission/key/etc...
        return HttpResponse("Insufficient permission")
    try:
        StoreItem.objects.get(name=item_key).delete()
    except (KeyError, StoreItem.DoesNotExist):
        pass
    return HttpResponseRedirect("/manage/overview")


@requires(superuser=True)
def request_catcher_overview(request):
    """
    Overview of all requests
    """

    try:
        distinct_ids: [] = RequestCatcherItem.objects.order_by().values("request_id").distinct()
    except RequestCatcherItem.DoesNotExist:
        distinct_ids = []

    catches = []

    for id_ in distinct_ids:
        length = RequestCatcherItem.objects.filter(request_id=id_["request_id"]).count()
        catches.append({
            "id": id_["request_id"],
            "length": length,
        })

    context = {
        "site": "request_catcher",
        "catches": catches
    }
    return render(request, "management/request_catcher_overview.html", context)


@requires(superuser=True)
def delete_request(request, request_id):
    """Delete a request by id"""

    try:
        catches = RequestCatcherItem.objects.filter(request_id=request_id)
    except RequestCatcherItem.DoesNotExist:
        pass

    catches.delete()

    return HttpResponseRedirect("/manage/request_catcher")


def random_string(string_length=10):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(string_length))
