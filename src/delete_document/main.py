# -*- coding: utf-8 -*-
"""
delete_document — API DELETE /doc/{documentid}

Deletes the document metadata, all of its conversation histories, and the
backing OBS objects (the PDF and the embeddings JSON).
"""
from common.event import get_user_id, get_path_param
from common import obs, dynamodb, response


def handler(event, context):
    user_id = get_user_id(event)
    document_id = get_path_param(event, "documentid")

    dt = dynamodb.document_table()
    resp = dt.get_item(Key={"userid": user_id, "documentid": document_id})
    if "Item" not in resp:
        return response.not_found()
    document = resp["Item"]

    mt = dynamodb.memory_table()
    with mt.batch_writer() as batch:
        for conv in document.get("conversations", []):
            batch.delete_item(
                Key={"userid": user_id, "SessionId": conv["conversationid"]}
            )
    dt.delete_item(Key={"userid": user_id, "documentid": document_id})

    filename = document["filename"]
    prefix = f"{user_id}/{filename}"
    obs.delete_objects([f"{prefix}/{filename}", f"{prefix}/index.json"])

    return response.ok({})
