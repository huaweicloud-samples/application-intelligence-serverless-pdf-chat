# -*- coding: utf-8 -*-
"""
upload_trigger — OBS ObjectCreated(.pdf) trigger.

Runs on the OBS upload event: records document metadata + the first
conversation in GeminiDB (DynamoDB-compatible) and counts PDF pages. The OBS
event is fanned out directly to generate_embeddings as well.

documentid is derived deterministically from the object key (uuid5) so both
this function and generate_embeddings agree on the id without coordination.
"""
import json
import os
from datetime import datetime, timezone
import uuid

from pypdf import PdfReader

from common.event import parse_obs_event
from common import obs, dynamodb


def _now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def handler(event, context):
    key, size = parse_obs_event(event)
    if not key or not key.lower().endswith(".pdf"):
        return {"statusCode": 200, "body": json.dumps({"skipped": "non-pdf"})}

    split = key.split("/")
    user_id = split[0]
    file_name = split[1]
    document_id = uuid.uuid5(uuid.NAMESPACE_URL, key).hex
    conversation_id = uuid.uuid4().hex
    ts = _now()

    local = f"/tmp/{file_name}"
    try:
        obs.download_file(key, local)
        reader = PdfReader(local)
        pages = str(len(reader.pages))
    except Exception:
        pages = "0"
    finally:
        if os.path.exists(local):
            os.remove(local)

    document = {
        "userid": user_id,
        "documentid": document_id,
        "filename": file_name,
        "created": ts,
        "pages": pages,
        "filesize": str(size),
        "docstatus": "UPLOADED",
        "conversations": [{"conversationid": conversation_id, "created": ts}],
    }
    dynamodb.document_table().put_item(Item=document)
    dynamodb.memory_table().put_item(
        Item={"userid": user_id, "SessionId": conversation_id, "History": []}
    )
    return {"statusCode": 200, "body": json.dumps({"documentid": document_id})}
