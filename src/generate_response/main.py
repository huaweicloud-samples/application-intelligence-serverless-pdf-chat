# -*- coding: utf-8 -*-
"""
generate_response — API POST /{documentid}/{conversationid}

Embeds the question via MaaS, picks the top-k chunks by cosine similarity,
feeds them as context to MaaS chat together with the stored conversation
history, and persists the new turn in GeminiDB. History keeps the
{type, data:{content}} shape the front end expects.
"""
import json
import os

from common.event import get_user_id, get_path_param, get_body
from common import obs, dynamodb, maas, cosine, response


def handler(event, context):
    user_id = get_user_id(event)
    document_id = get_path_param(event, "documentid")
    conversation_id = get_path_param(event, "conversationid")
    body = get_body(event)
    file_name = body.get("fileName")
    prompt = body.get("prompt")
    if not file_name or not prompt:
        return response.bad_request("fileName and prompt are required")

    index_key = f"{user_id}/{file_name}/index.json"
    local = "/tmp/index.json"
    try:
        obs.download_file(index_key, local)
    except Exception:
        return response.bad_request("Document not ready or not found")
    with open(local, encoding="utf-8") as f:
        index = json.load(f)
    if os.path.exists(local):
        os.remove(local)

    chunks = index["chunks"]
    embeddings = index["embeddings"]
    if not chunks:
        return response.bad_request("Document has no extractable text")

    query_vec = maas.embed([prompt])[0]
    top_idx = cosine.top_k(query_vec, embeddings, k=4)
    context_text = "\n\n".join(chunks[i] for i in top_idx)

    mt = dynamodb.memory_table()
    resp = mt.get_item(Key={"userid": user_id, "SessionId": conversation_id})
    history = resp.get("Item", {}).get("History", []) if "Item" in resp else []

    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that answers questions based ONLY "
                "on the provided document context. If the context does not "
                "contain the answer, say you don't know."
            ),
        }
    ]
    for h in history:
        role = "user" if h.get("type") == "human" else "assistant"
        messages.append({"role": role, "content": h["data"]["content"]})
    messages.append(
        {
            "role": "user",
            "content": f"Document context:\n{context_text}\n\nQuestion: {prompt}",
        }
    )

    answer = maas.chat(messages)

    history.append(
        {
            "type": "human",
            "data": {"content": prompt, "additional_kwargs": {}, "example": False},
        }
    )
    history.append(
        {
            "type": "ai",
            "data": {"content": answer, "additional_kwargs": {}, "example": False},
        }
    )
    mt.update_item(
        Key={"userid": user_id, "SessionId": conversation_id},
        UpdateExpression="SET History = :h",
        ExpressionAttributeValues={":h": history},
    )
    return response.ok({"answer": answer})
