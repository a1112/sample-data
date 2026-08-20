#!/usr/bin/env python3
import argparse
import base64
import hashlib
import json
from pathlib import Path

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

parser = argparse.ArgumentParser(description="Assemble and verify the steel inspection sample-data bundle.")
parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent)
parser.add_argument("--output", type=Path, default=Path("steel-inspection-sample-data.zip"))
args = parser.parse_args()
manifest = json.loads((args.root / "bundle-manifest.json").read_text(encoding="utf-8"))
archive = args.root / "archive-b64"
with args.output.open("wb") as target:
    for part in manifest["parts"]:
        path = archive / part["name"]
        encoded = path.read_text(encoding="ascii")
        if len(encoded) != part["encodedSize"]:
            raise SystemExit(f"encoded size mismatch: {path}")
        data = base64.b64decode(encoded, validate=True)
        if len(data) != part["size"]:
            raise SystemExit(f"decoded size mismatch: {path}")
        if sha256_bytes(data) != part["sha256"]:
            raise SystemExit(f"sha256 mismatch: {path}")
        target.write(data)
if args.output.stat().st_size != manifest["artifactSize"]:
    raise SystemExit("assembled artifact size mismatch")
if sha256_file(args.output) != manifest["artifactSha256"]:
    raise SystemExit("assembled artifact sha256 mismatch")
print(f"verified {args.output}")
