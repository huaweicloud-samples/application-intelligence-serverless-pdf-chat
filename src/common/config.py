# -*- coding: utf-8 -*-
"""
Centralised configuration.

All credentials are injected at deploy time through FunctionGraph environment
variables (populated from Terraform sensitive variables). Nothing secret is
ever written to disk or committed to the repository. The GeminiDB
DynamoDB-compatible interface reuses the DynamoDB wire protocol: it talks
DynamoDB-compatible protocol over a custom endpoint with the instance's `rwuser` account
and instance password (port 80 on the load-balancer endpoint).
"""
import os


def _env(name, default=""):
    return os.environ.get(name, default)


# --- OBS (object storage, accessed via built-in ObsClient) ---
OBS_BUCKET = _env("OBS_BUCKET")
OBS_ENDPOINT = _env("OBS_ENDPOINT")          # e.g. https://obs.cn-north-4.myhuaweicloud.com
OBS_REGION = _env("OBS_REGION", "cn-north-4")
OBS_ACCESS_KEY = _env("OBS_ACCESS_KEY")
OBS_SECRET_KEY = _env("OBS_SECRET_KEY")

# --- GeminiDB (DynamoDB-compatible interface) ---
GEMINIDB_ENDPOINT = _env("GEMINIDB_ENDPOINT")   # e.g. http://10.x.x.x:80
GEMINIDB_USER = _env("GEMINIDB_USER", "rwuser")
GEMINIDB_PASSWORD = _env("GEMINIDB_PASSWORD")
GEMINIDB_REGION = _env("GEMINIDB_REGION", "cn-north-4")

DOCUMENT_TABLE = _env("DOCUMENT_TABLE", "DocumentTable")
MEMORY_TABLE = _env("MEMORY_TABLE", "MemoryTable")

# --- MaaS (ModelArts inference, OpenAI-compatible) ---
# OpenAI-compatible base, e.g. https://api.modelarts-maas.com/openai/v1
MAAS_ENDPOINT = _env("MAAS_ENDPOINT")
MAAS_API_KEY = _env("MAAS_API_KEY")
MAAS_EMBEDDING_MODEL = _env("MAAS_EMBEDDING_MODEL")
MAAS_CHAT_MODEL = _env("MAAS_CHAT_MODEL")

LOG_LEVEL = _env("LOG_LEVEL", "INFO")

# Application authentication (C21 mode B): Cognito user pool is replaced by
# APIG App authentication. The frontend carries a per-browser user id in the
# X-User-Id header so documents stay scoped per user (replacing the Cognito
# `sub` claim). APIG enforces the AppKey/AppSecret boundary in front of the
# function, so the function only needs the user id for data partitioning.
USER_ID_HEADER = "X-User-Id"
