from django.db import models


# Create your models here.
class Permission(models.Model):
    name = models.CharField(unique=True, max_length=200)


class ApiKey(models.Model):
    name = models.CharField(max_length=200, default="API Key")
    value = models.CharField(unique=True, max_length=200)
    permission = models.ManyToManyField(Permission)


class StoreItem(models.Model):
    name = models.CharField(unique=True, max_length=200)
    value = models.TextField()
    confidential = models.BooleanField(default=False)


class WebsocketClients(models.Model):
    identifier = models.CharField(max_length=500)
    channel_name = models.CharField(max_length=200)
    scopes = models.JSONField(null=True, default=list)


class KITRoomAddressCache(models.Model):
    building_id = models.CharField(max_length=200, primary_key=True)
    # address = models.CharField(max_length=200)
    google_maps_link = models.CharField(max_length=200)


class URLShortener(models.Model):
    short_id = models.CharField(max_length=200, primary_key=True)
    url = models.CharField(max_length=20000)


class RequestCatcherItem(models.Model):
    request_id = models.CharField(max_length=200)
    ip_address = models.CharField(max_length=200, default="")
    timestamp = models.DateTimeField(auto_now_add=True)
    content_type = models.CharField(max_length=200)
    request_method = models.CharField(max_length=200)
    request_headers = models.TextField()
    raw_request_headers = models.TextField()
    request_body = models.TextField()

    def as_json(self):
        return {
            "request_id": self.request_id,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp,
            "content_type": self.content_type,
            "request_method": self.request_method,
            "request_headers": self.request_headers,
            "raw_request_headers": self.raw_request_headers,
            "request_body": self.request_body
        }


class ImageTag(models.Model):
    id = models.CharField(max_length=200, primary_key=True)
    title = models.CharField(max_length=200)
    # image = models.ImageField(upload_to='images/')


class Image(models.Model):
    # id = models.CharField(max_length=200, primary_key=True)
    title = models.CharField(max_length=200, default="")
    image = models.ImageField(upload_to='images/')
    tags = models.ManyToManyField(ImageTag)
