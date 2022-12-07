from typing import Optional

from api.models import URLShortener
from api.util import utils


def create_or_edit(url: str, short_id: Optional[str] = None):
    """Generates a short link id for the given url"""

    if short_id is None:
        existing_ids = [o.short_id for o in URLShortener.objects.all()]
        short_id = utils.random_string(5)
        while short_id in existing_ids:
            short_id = utils.random_string(5)

    if not URLShortener.objects.filter(short_id=short_id).exists():
        URLShortener(short_id=short_id, url=url).save()
    else:
        URLShortener.objects.filter(short_id=short_id).update(url=url)

    return short_id


def resolve(short_id: str):
    """Resolves a short link id to the original url"""
    if not short_id:
        return None

    try:
        short = URLShortener.objects.get(short_id=short_id)
        return short.url
    except URLShortener.DoesNotExist:
        return None
