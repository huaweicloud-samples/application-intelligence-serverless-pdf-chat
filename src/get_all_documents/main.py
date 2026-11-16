# -*- coding: utf-8 -*-
"""
get_all_documents — API GET /doc

Lists all documents for the current user, newest first.
"""
from boto3.dynamodb.conditions import Key

from common.event import get_user_id
from common import dynamodb, response


def handler(event, context):
    user_id = get_user_id(event)
    resp = dynamodb.document_table().query(
        KeyConditionExpression=Key("userid").eq(user_id)
    )
    items = sorted(
        resp.get("Items", []),
        key=lambda i: i.get("created", ""),
        reverse=True,
    )
    for item in items:
        item["conversations"] = sorted(
            item.get("conversations", []),
            key=lambda c: c.get("created", ""),
            reverse=True,
        )
    return response.ok(items)
