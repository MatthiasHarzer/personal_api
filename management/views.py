from django.shortcuts import render

import random
import string

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render

from .forms import *
from api.models import *


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


def delete_store_item(request, item_key):
    if not request.user.is_superuser:  # Only su can create new permission/key/etc...
        return HttpResponse("Insufficient permission")
    try:
        StoreItem.objects.get(name=item_key).delete()
    except (KeyError, StoreItem.DoesNotExist):
        pass
    return HttpResponseRedirect("/manage/overview")


def random_string(string_length=10):
    letters = string.ascii_letters
    return ''.join(random.choice(letters) for _ in range(string_length))
