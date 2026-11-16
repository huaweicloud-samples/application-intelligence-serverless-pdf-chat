# -*- coding: utf-8 -*-
"""
APIG -> FunctionGraph event helpers.

When APIG (Huawei Cloud API Gateway) invokes a FunctionGraph function it
delivers an HTTP-proxy style event. We normalise the few fields the handlers
need and, importantly, recover the per-user identity.

Cognito's `requestContext.authorizer.claims.sub` is gone (C21 mode B). The
APIG App authentication boundary is enforced in front of the function, so the
function only needs a stable per-browser user id to partition documents. The
frontend supplies it in the `X-User-Id` header; if absent we fall back to the
calling app id, then to a shared anonymous id.
"""
import base64
import json

from common import config


def get_headers(event):
    return {k.lower(): v for k, v in (event.get("headers") or {}).items()}


def get_header(event, name):
    return get_headers(event).get(name.lower())


def get_query(event, name):
    return (event.get("queryStringParameters") or {}).get(name)


def get_path_param(event, name):
    return (event.get("pathParameters") or {}).get(name)


def get_body(event):
    body = event.get("body")
    if isinstance(body, str):
        if event.get("isBase64Encoded"):
            body = base64.b64decode(body).decode("utf-8")
        try:
            return json.loads(body)
        except Exception:
            return {}
    return body or {}


def get_user_id(event):
    uid = get_header(event, config.USER_ID_HEADER)
    if uid:
        return uid
    rc = event.get("requestContext") or {}
    return rc.get("appId") or "anonymous"


def parse_obs_event(event):
    """Return (object_key, size) from an OBS -> FunctionGraph trigger event."""
    record = event["Records"][0]
    obj = record["obs"]["object"]
    key = obj["key"]
    size = int(obj.get("size", 0))
    return key, size
