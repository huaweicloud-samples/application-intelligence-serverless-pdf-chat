# -*- coding: utf-8 -*-
"""
generate_presigned_url — API GET /generate_presigned_url?file_name=<name>

Issues an OBS presigned PUT URL using the built-in OBS SDK (ObsClient). The
object key keeps the layout {user_id}/{file_name}.pdf/{file_name}.pdf so the
upload event can be parsed by the downstream triggers.
"""
import uuid

from common.event import get_user_id, get_query
from common import obs, response


def handler(event, context):
    user_id = get_user_id(event)
    file_name_full = get_query(event, "file_name")
    if not file_name_full:
        return response.bad_request("file_name is required")

    file_name = file_name_full.split(".pdf")[0]
    exists = obs.object_exists(f"{user_id}/{file_name_full}/{file_name_full}")
    if exists:
        suffix = uuid.uuid4().hex[:4]
        key = f"{user_id}/{file_name}-{suffix}.pdf/{file_name}-{suffix}.pdf"
    else:
        key = f"{user_id}/{file_name}.pdf/{file_name}.pdf"

    url = obs.generate_presigned_put_url(key)
    return response.ok({"presignedurl": url})
