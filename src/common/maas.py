# -*- coding: utf-8 -*-
"""
MaaS (ModelArts inference) client — OpenAI-compatible interface.

Huawei Cloud MaaS exposes an OpenAI-compatible API
(/v1/embeddings and /v1/chat/completions). We use the standard library
urllib so no extra HTTP dependency is required. Embedding and chat models
are selected through the `model` request field.
"""
import json
import urllib.request

from common import config


def _post(path, payload):
    url = config.MAAS_ENDPOINT.rstrip("/") + path
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer " + config.MAAS_API_KEY)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def embed(texts):
    """Return a list of embedding vectors (one per input text)."""
    if isinstance(texts, str):
        texts = [texts]
    body = {"model": config.MAAS_EMBEDDING_MODEL, "input": texts}
    result = _post("/embeddings", body)
    # OpenAI-compatible: data[i].embedding
    ordered = sorted(result["data"], key=lambda d: d["index"])
    return [d["embedding"] for d in ordered]


def chat(messages, temperature=0.0, max_tokens=1024):
    """messages: list of {"role": "system"/"user"/"assistant", "content": ...}."""
    body = {
        "model": config.MAAS_CHAT_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    result = _post("/chat/completions", body)
    return result["choices"][0]["message"]["content"]
