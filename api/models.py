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


