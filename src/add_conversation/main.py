# -*- coding: utf-8 -*-
"""
add_conversation — API POST /doc/{documentid}

Creates a new conversation under an existing document and returns its id.
"""
import uuid
from datetime import datetime, timezone

from common.event import get_user_id, get_path_param
from common import dynamodb, response


def handler(event, context):
    user_id = get_user_id(event)
    document_id = get_path_param(event, "documentid")

    dt = dynamodb.document_table()
    resp = dt.get_item(Key={"userid": user_id, "documentid": document_id})
    if "Item" not in resp:
        return response.not_found()

    conversations = resp["Item"].get("conversations", [])
    conversation_id = uuid.uuid4().hex
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    conversations.append({"conversationid": conversation_id, "created": ts})
    dt.update_item(
        Key={"userid": user_id, "documentid": document_id},
        UpdateExpression="SET conversations = :c",
        ExpressionAttributeValues={":c": conversations},
    )
    dynamodb.memory_table().put_item(
        Item={"userid": user_id, "SessionId": conversation_id, "History": []}
    )
    return response.ok({"conversationid": conversation_id})
