# -*- coding: utf-8 -*-
"""
Uniform HTTP response shape for APIG -> FunctionGraph.

APIG expects the function to return statusCode / headers / body. CORS headers
are returned from the function as a safety net in addition to the APIG CORS
policy so the OBS static-website front end can call the API cross-origin.
"""
import json


def response(status_code, body, cors="*"):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": cors,
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*",
        },
        "body": json.dumps(body, ensure_ascii=False, default=str),
        "isBase64Encoded": False,
    }


def ok(body):
    return response(200, body)


def created(body):
    return response(201, body)


def bad_request(msg):
    return response(400, {"error": msg})


def forbidden():
    return response(403, {"error": "forbidden"})


def not_found():
    return response(404, {"error": "not found"})
