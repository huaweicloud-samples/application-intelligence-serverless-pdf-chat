# -*- coding: utf-8 -*-
"""
GeminiDB (DynamoDB-compatible interface) client wrapper.

The DynamoDB-compatible interface of GeminiDB is reached with the standard
DynamoDB-compatible wire protocol pointed at the instance load-balancer endpoint. Tables are
provisioned (PAY_PER_REQUEST is rejected by the compatible interface), so we
create them with 1 read / 1 write unit idempotently on first use.
"""
import boto3
from botocore.exceptions import ClientError

from common import config


def _resource():
    return boto3.resource(
        "dynamodb",
        endpoint_url=config.GEMINIDB_ENDPOINT,
        region_name=config.GEMINIDB_REGION,
        aws_access_key_id=config.GEMINIDB_USER,
        aws_secret_access_key=config.GEMINIDB_PASSWORD,
    )


def _ensure_table(name, key_schema, attribute_definitions):
    try:
        _resource().create_table(
            TableName=name,
            KeySchema=key_schema,
            AttributeDefinitions=attribute_definitions,
            BillingMode="PROVISIONED",
            ProvisionedThroughput={
                "ReadCapacityUnits": 1,
                "WriteCapacityUnits": 1,
            },
        )
    except ClientError as e:
        # ResourceInUseException => table already exists; safe to ignore.
        if e.response.get("Error", {}).get("Code") != "ResourceInUseException":
            raise


def ensure_schema():
    """Create both tables if they do not yet exist (idempotent)."""
    _ensure_table(
        config.DOCUMENT_TABLE,
        key_schema=[
            {"AttributeName": "userid", "KeyType": "HASH"},
            {"AttributeName": "documentid", "KeyType": "RANGE"},
        ],
        attribute_definitions=[
            {"AttributeName": "userid", "AttributeType": "S"},
            {"AttributeName": "documentid", "AttributeType": "S"},
        ],
    )
    _ensure_table(
        config.MEMORY_TABLE,
        key_schema=[
            {"AttributeName": "userid", "KeyType": "HASH"},
            {"AttributeName": "SessionId", "KeyType": "RANGE"},
        ],
        attribute_definitions=[
            {"AttributeName": "userid", "AttributeType": "S"},
            {"AttributeName": "SessionId", "AttributeType": "S"},
        ],
    )


def document_table():
    ensure_schema()
    return _resource().Table(config.DOCUMENT_TABLE)


def memory_table():
    ensure_schema()
    return _resource().Table(config.MEMORY_TABLE)
