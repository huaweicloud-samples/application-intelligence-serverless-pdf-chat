# -*- coding: utf-8 -*-
"""
OBS client wrapper.

Uses the built-in OBS SDK (esdk-obs-python) which is pre-installed in the
FunctionGraph Python runtime. This is the ONLY supported way to access OBS
from FGS - using boto3 to OBS will hit the C5 gateway and FAIL.
"""
from obs import ObsClient

from common import config


def _client():
    # Use explicit credentials from config (set via user_data in Terraform)
    # The agency (op_svc_cff) grants OBS OperateAccess role to the function,
    # so the function can access OBS with these credentials.
    return ObsClient(
        access_key_id=config.OBS_ACCESS_KEY,
        secret_access_key=config.OBS_SECRET_KEY,
        server=config.OBS_ENDPOINT,
        signature="v4",
    )


def object_exists(key):
    try:
        resp = _client().headObject(bucket_name=config.OBS_BUCKET, object_key=key)
        return resp.status < 300
    except Exception:
        return False


def generate_presigned_put_url(key, expires=300, content_type="application/pdf"):
    # OBS pre-signed URL via SDK
    client = _client()
    # Generate signed URL for PUT operation
    resp = client.createSignedUrl(
        bucket_name=config.OBS_BUCKET,
        object_key=key,
        method="PUT",
        expires=expires,
        headers={"Content-Type": content_type},
    )
    if resp.status >= 300:
        raise Exception(f"Failed to generate signed URL: {resp.errorMessage}")
    return resp.body


def download_file(key, local_path):
    resp = _client().getObject(
        bucket_name=config.OBS_BUCKET,
        object_key=key,
        downloadPath=local_path,
    )
    if resp.status >= 300:
        raise Exception(f"Failed to download {key}: {resp.errorMessage}")


def upload_file(local_path, key):
    resp = _client().putFile(
        bucket_name=config.OBS_BUCKET,
        object_key=key,
        file_path=local_path,
    )
    if resp.status >= 300:
        raise Exception(f"Failed to upload {key}: {resp.errorMessage}")


def delete_objects(keys):
    if not keys:
        return
    # OBS deleteObjects supports deleting multiple objects in one call
    objects = [{"key": k} for k in keys]
    resp = _client().deleteObjects(
        bucket_name=config.OBS_BUCKET,
        delete=[{"key": k} for k in keys],
        quiet=True,
    )
    if resp.status >= 300:
        raise Exception(f"Failed to delete objects: {resp.errorMessage}")
