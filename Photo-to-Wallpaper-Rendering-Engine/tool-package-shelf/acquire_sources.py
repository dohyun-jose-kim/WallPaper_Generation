"""Fetch only inspected files from immutable revisions; never execute upstream scripts."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args()
    shelf = Path(__file__).resolve().parent
    manifest = json.loads((shelf / "source-manifest.json").read_text())
    count = 0
    for source in manifest["sources"]:
        for record in source["files"]:
            target = shelf / "upstream" / source["id"] / record["path"]
            if target.exists():
                data = target.read_bytes()
            elif args.verify_only:
                raise FileNotFoundError(target)
            else:
                request = urllib.request.Request(record["url"], headers={
                    "User-Agent": "wallpaper-build-preparation"
                })
                with urllib.request.urlopen(request, timeout=60) as response:
                    data = response.read()
            if hashlib.sha256(data).hexdigest() != record["sha256"]:
                raise ValueError(f"Source hash mismatch: {source['id']}/{record['path']}")
            if not target.exists():
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data)
            count += 1
    print(f"Verified {count} unchanged upstream files at pinned revisions.")


if __name__ == "__main__":
    main()
