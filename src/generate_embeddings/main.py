# -*- coding: utf-8 -*-
"""
generate_embeddings — OBS ObjectCreated(.pdf) trigger.

Extracts text with pypdf, chunks it, embeds the chunks via MaaS
(OpenAI-compatible /v1/embeddings), and stores the chunks + vectors as JSON in
OBS. Retrieval is pure-Python cosine similarity (see common/cosine.py), so no
heavy vector-search dependency is required.

documentid is derived from the object key (uuid5), matching upload_trigger, so
no cross-function coordination is needed.
"""
import json
import os
import time
import uuid

from pypdf import PdfReader

from common.event import parse_obs_event
from common import obs, dynamodb, maas, cosine


def _set_status(document_id, user_id, status):
    try:
        dynamodb.document_table().update_item(
            Key={"userid": user_id, "documentid": document_id},
            UpdateExpression="SET docstatus = :s",
            ExpressionAttributeValues={":s": status},
            ConditionExpression="attribute_exists(documentid)",
        )
        return True
    except Exception:
        return False


def handler(event, context):
    key, _size = parse_obs_event(event)
    if not key or not key.lower().endswith(".pdf"):
        return {"statusCode": 200, "body": json.dumps({"skipped": "non-pdf"})}

    split = key.split("/")
    user_id = split[0]
    file_name_full = split[-1]
    document_id = uuid.uuid5(uuid.NAMESPACE_URL, key).hex

    local = f"/tmp/{file_name_full}"
    obs.download_file(key, local)

    text_parts = []
    try:
        reader = PdfReader(local)
        for page in reader.pages:
            text_parts.append(page.extract_text() or "")
    except Exception as e:
        return {"statusCode": 200, "body": json.dumps({"error": str(e)})}
    finally:
        if os.path.exists(local):
            os.remove(local)

    full_text = "\n".join(text_parts)
    chunks = cosine.chunk_text(full_text, chunk_size=1000, overlap=100)
    if not chunks:
        _set_status(document_id, user_id, "READY")
        return {"statusCode": 200, "body": json.dumps({"chunks": 0})}

    embeddings = maas.embed(chunks)

    index_local = "/tmp/index.json"
    with open(index_local, "w", encoding="utf-8") as f:
        json.dump({"chunks": chunks, "embeddings": embeddings}, f)
    obs.upload_file(index_local, f"{user_id}/{file_name_full}/index.json")
    if os.path.exists(index_local):
        os.remove(index_local)

    # Best-effort PROCESSING, then reliably flip to READY once upload_trigger
    # has created the document item (deterministic id => no race on the read).
    _set_status(document_id, user_id, "PROCESSING")
    for _ in range(30):
        if _set_status(document_id, user_id, "READY"):
            break
        time.sleep(2)

    return {
        "statusCode": 200,
        "body": json.dumps({"documentid": document_id, "chunks": len(chunks)}),
    }
