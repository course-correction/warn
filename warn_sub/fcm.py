"""
fcm.py takes the information provided by the NINA web app and uses it to connect to firebase cloud messaging.

It handles initial registration and maintains the credentials returned by firebase.
"""

import logging
from pathlib import Path
from typing import Any
from firebase_messaging import FcmPushClient, FcmPushClientConfig, FcmRegisterConfig
import json
import nina

logger = logging.getLogger(__name__)


def get_push_client(on_notification):
    fcm_config = _get_fcm_config()
    fcm_credentials = _get_fcm_credentials()

    return FcmPushClient(
        on_notification,
        fcm_config,
        fcm_credentials,
        _on_credentials_updated,
    )


_CREDENTIALS_FILE = Path("fcm_credentials.json")


def _get_fcm_credentials() -> dict[str, Any] | None:
    if not _CREDENTIALS_FILE.exists():
        return {}

    with open(_CREDENTIALS_FILE) as f:
        return json.load(f)


def _get_fcm_config() -> FcmRegisterConfig:
    c = nina.get_fcm_credentials()
    return FcmRegisterConfig(
        c.fcm_project_id, c.fcm_app_id, c.fcm_api_key, c.fcm_message_sender_id
    )


def _on_credentials_updated(new_credentials: dict[str, Any]):
    with open(_CREDENTIALS_FILE, mode="w") as f:
        json.dump(new_credentials, f, indent=4)
