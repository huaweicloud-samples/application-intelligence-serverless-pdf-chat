# -*- coding: utf-8 -*-
"""
Build packaging for FunctionGraph.

Each function is packaged as a zip containing:
  - main.py            (the handler)
  - common/            (shared OBS / GeminiDB / MaaS / cosine / event / response)
  - <vendor packages>  (boto3 for GeminiDB, pypdf) installed with `pip install -t`

Run:  python src/build.py
Output: src/dist/<function>.zip   (referenced by infra/main.tf OBS object)

Note: OBS access uses the built-in esdk-obs-python (pre-installed in FGS runtime),
not boto3. boto3 is only for GeminiDB DynamoDB-compatible interface.
"""
import os
import shutil
import subprocess
import sys
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
VENDOR = os.path.join(HERE, "vendor")
DIST = os.path.join(HERE, "dist")

FUNCTIONS = [
    "generate_presigned_url",
    "upload_trigger",
    "get_document",
    "get_all_documents",
    "add_conversation",
    "generate_embeddings",
    "generate_response",
    "delete_document",
]

REQUIREMENTS = os.path.join(HERE, "requirements.txt")


def install_vendor(force=False):
    if os.path.isdir(VENDOR) and not force:
        print("vendor already present, skipping pip install (use --force to rebuild)")
        return
    if os.path.isdir(VENDOR):
        shutil.rmtree(VENDOR)
    os.makedirs(VENDOR, exist_ok=True)
    subprocess.check_call(
        [sys.executable, "-m", "pip", "install", "-t", VENDOR, "-r", REQUIREMENTS]
    )


def _zip_add_dir(zf, base_dir, arc_root):
    for root, _dirs, files in os.walk(base_dir):
        for fname in files:
            if fname.endswith(".pyc") or fname.startswith("."):
                continue
            fp = os.path.join(root, fname)
            arcname = os.path.relpath(fp, arc_root)
            zf.write(fp, arcname)


def build_function(func):
    func_dir = os.path.join(HERE, func)
    zip_path = os.path.join(DIST, func + ".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # handler
        zf.write(os.path.join(func_dir, "main.py"), "main.py")
        # shared common package
        _zip_add_dir(zf, os.path.join(HERE, "common"), HERE)
        # vendored dependencies at zip root
        _zip_add_dir(zf, VENDOR, VENDOR)
    size = os.path.getsize(zip_path)
    print(f"  built {func}.zip ({size // 1024} KB)")


def main():
    force = "--force" in sys.argv
    install_vendor(force=force)
    os.makedirs(DIST, exist_ok=True)
    print(f"packaging {len(FUNCTIONS)} functions -> {DIST}")
    for func in FUNCTIONS:
        build_function(func)
    print("done")


if __name__ == "__main__":
    main()
