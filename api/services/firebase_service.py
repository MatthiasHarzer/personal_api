import os
from typing import Optional

from firebase_admin import credentials, firestore
import firebase_admin
from firebase_dynamic_links import DynamicLinks

from api import secrets

PATH = os.path.dirname(os.path.realpath(__file__))

cred = credentials.Certificate(f"{PATH}/firebase-service-account.json")
firebase_admin.initialize_app(cred)


def get_user_id_by_dynlink(link: str) -> Optional[str]:
    """
    Tries to fetch the user with the given dynLink from the firestore and returns its uid.
    If no user was found, None is returned.
    """
    db = firestore.client()
    users = db.collection("wg-it/public/users")
    for user in users.where("dynLink", "==", link).stream():
        if user.to_dict().get("dynLink") == link:
            return user.id
    return None


def create_dynamic_link_for_user(user_id: str) -> str:
    """
    Creates a dynamic link for the given user and returns it.
    """
    dl = DynamicLinks(api_key=secrets.FIREBASE_API_KEY, domain=secrets.DYNLINK_URI_PREFIX)
    target_link = f"https://wgit.taptwice.dev/?user={user_id}"
    params = {
        "androidInfo": {
            "androidPackageName": "dev.taptwice.wgit",
            "androidFallbackLink": target_link,
        }
    }

    return dl.generate_dynamic_link(target_link, params=params)
