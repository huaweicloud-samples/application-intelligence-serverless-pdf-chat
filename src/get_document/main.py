# -*- coding: utf-8 -*-
"""
get_document — API GET /doc/{documentid}/{conversationid}

Returns the document metadata, its conversation list, and the chat history for
the requested conversation. The History attribute carries LangChain-compatible
message objects ({type, data:{content,...}}) so the front end renders unchanged.
"""
from common.event import get_user_id, get_path_param
from common import dynamodb, response


def handler(event, context):
    user_id = get_user_id(event)
    document_id = get_path_param(event, "documentid")
    conversation_id = get_path_param(event, "conversationid")

    resp = dynamodb.document_table().get_item(
        Key={"userid": user_id, "documentid": document_id}
    )
    if "Item" not in resp:
        return response.not_found()
    document = resp["Item"]
    document["conversations"] = sorted(
        document.get("conversations", []),
        key=lambda c: c.get("created", ""),
        reverse=True,
    )

    resp2 = dynamodb.memory_table().get_item(
        Key={"userid": user_id, "SessionId": conversation_id}
    )
    if "Item" not in resp2:
        return response.forbidden()
    messages = resp2["Item"].get("History", [])

    return response.ok(
        {
            "conversationid": conversation_id,
            "document": document,
            "messages": messages,
        }
    )
