"""
nina.py encapsualtes everything implementation specific of the NINA web app.
This is:
  a) Extraction of deployment config for various fcm and nina backend credentials.
  b) Communication with NINA push server for configuration of push messages after registration with firebase.
  c) Parsing of push events
  d) Retrieval of further event details from a push event
"""

from __future__ import annotations
import base64
from pathlib import Path
from typing import NamedTuple
import logging
from uuid import UUID, uuid4
import requests
import json
from pydantic import BaseModel, Field, AliasPath

logger = logging.getLogger(__name__)


class FCMCredentials(NamedTuple):
    fcm_project_id: str
    fcm_app_id: str
    fcm_api_key: str
    fcm_message_sender_id: str

    @staticmethod
    def from_nina(nc: _NinaConfig) -> FCMCredentials:
        return FCMCredentials(
            nc.fb_project_id, nc.fb_app_id, nc.fb_api_key, nc.fb_message_sender_id
        )


class _NinaConfig(BaseModel):
    fb_project_id: str = Field(
        validation_alias=AliasPath("firebaseConfig", "projectId")
    )
    fb_app_id: str = Field(validation_alias=AliasPath("firebaseConfig", "appId"))
    fb_api_key: str = Field(validation_alias=AliasPath("firebaseConfig", "apiKey"))
    fb_message_sender_id: str = Field(
        validation_alias=AliasPath("firebaseConfig", "messagingSenderId")
    )

    npns_user: str = Field(validation_alias=AliasPath("npnsConfig", "user"))
    npns_pass: str = Field(validation_alias=AliasPath("npnsConfig", "password"))


def get_fcm_credentials() -> FCMCredentials:
    nina_config = _get_nina_config()
    return FCMCredentials.from_nina(nina_config)


_NINA_REGION_CODES_URL = "https://warnung.bund.de/assets/json/converted_gemeinden.json"


def get_region_codes() -> list[int]:
    logging.info("Downloading all region codes...")
    r = requests.get(_NINA_REGION_CODES_URL)
    data = r.json()
    regions = []

    for key in data.keys():
        regions.append(int(key))

    return regions


_NINA_PREFERENCES_TEMPLATE = {
    "preferences": [
        {"name": "regions", "type": "INTEGER_ARRAY", "value": None},
        {"name": "regionParts", "type": "INTEGER_ARRAY", "value": None},
        {"name": "mowasLevel", "type": "INTEGER", "value": "4"},
        {"name": "dwdLevel", "type": "INTEGER", "value": "4"},
        {"name": "lhpLevel", "type": "INTEGER", "value": "4"},
    ]
}

_API_HOST = "https://push.warnung.bund.de/v1/nina-3-1/"


def configure_push(fcm_token: str, region_codes: list[int]):
    client_id = _get_client_id()
    client_id = str(client_id)
    nina_config = _get_nina_config()

    auth_str = f"{nina_config.npns_user}:{nina_config.npns_pass}"
    auth_bytes = auth_str.encode("utf-8")
    auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Basic {auth_b64}",
    }

    url_get_preferences = f"{_API_HOST}preference/{client_id}"
    url_put_register = f"{_API_HOST}address/web/{client_id}"
    url_put_preferences = f"{_API_HOST}preference/{client_id}"

    res = requests.get(url_get_preferences, headers=headers)

    if res.status_code == 404:
        logger.info("Registering new NINA instance")

        body = {
            "token": fcm_token,
        }
        res = requests.put(url_put_register, headers=headers, json=body)

        if res.status_code != 200:
            logger.error("Could not register new NINA instance")
            raise Exception(res.text)

    logger.info("Setting subscription options for regions")

    body = _NINA_PREFERENCES_TEMPLATE
    regions = ",".join(map(str, region_codes))
    regions = f"[{regions}]"
    for elem in body["preferences"]:
        if elem["name"] == "regions" or elem["name"] == "regionParts":
            elem["value"] = regions

    res = requests.put(url_put_preferences, json=body, headers=headers)

    if res.status_code != 200:
        logger.error("Could set NINA push preferences")
        raise Exception(res.text)


class NinaPushMsg(BaseModel):
    """Ignores many members"""

    id: str
    msgType: str | None = Field(default=None, validation_alias=AliasPath("data", "msgType"))
    headline: str | None = Field(default=None, validation_alias=AliasPath("data", "headline"))
    provider: str | None = Field(default=None, validation_alias=AliasPath("data", "provider"))
    severity: str | None = Field(default=None, validation_alias=AliasPath("data", "severity"))
    event_code: str | None = Field(default=None, validation_alias=AliasPath("data", "transKeys", "event"))


def parse_push_msg(msg: dict):
    return NinaPushMsg.model_validate(msg)


_NINA_EVENT_URL = "https://warnung.bund.de/api31/warnings/"


def get_event_raw(id: str) -> dict:
    res = requests.get(f"{_NINA_EVENT_URL}{id}.json")
    return res.json()


class NinaEvent(BaseModel):
    identifier: str
    headline: str | None
    description: str | None
    instruction: str | None
    link: str


def parse_event(event: dict) -> NinaEvent:
    identifier = event["identifier"]
    headline = None
    description = None
    instruction = None
    link = f"https://warnung.bund.de/meldungen/{identifier}"
    
    if "info" in event:
        for info in event["info"].values():
            if info["language"] not in ["DE", "de-DE"]:
                continue
            
            headline = info.get("headline")
            description = info.get("description")
            instruction = info.get("instruction")
            
            break

    return NinaEvent(
        identifier=identifier,
        headline=headline,
        description=description,
        instruction=instruction,
        link=link,
    )


_NINA_ID_FILE = Path("nina_id.json")


def _get_client_id() -> UUID:
    if _NINA_ID_FILE.exists():
        with open(_NINA_ID_FILE, "r") as f:
            nina_id = json.load(f)
            logger.debug(f"loaded nina id '{nina_id}' from file")
            return UUID(nina_id)
    else:
        nina_id = uuid4()
        with open(_NINA_ID_FILE, "w") as f:
            f.write(json.dumps(str(nina_id)))

        logger.debug(f"generated new nina id '{nina_id}'")
        return nina_id


_NINA_CONFIG_FILE = Path("nina_config.json")


def _get_nina_config() -> _NinaConfig:
    if _NINA_CONFIG_FILE.exists():
        with open(_NINA_CONFIG_FILE, "r") as f:
            return _NinaConfig.model_validate(json.load(f), by_name=True)
    else:
        logger.info("Nina config file not present. Dowloading...")
        return _download_nina_config()


_NINA_CONFIG_URL = "https://warnung.bund.de/assets/json/config.json"


def _download_nina_config():
    res = requests.get(_NINA_CONFIG_URL)
    res = res.json()

    parsed_model = _NinaConfig.model_validate(res)

    with open(_NINA_CONFIG_FILE, "w") as f:
        f.write(parsed_model.model_dump_json(indent=4))

    return parsed_model
