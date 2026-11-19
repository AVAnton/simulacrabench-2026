"""Prepare the pinned Kumo checkpoint for local, offline competition checks."""

import argparse
import hashlib
import json
import os
import shutil
import tempfile
import urllib.request
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, required=True,
                        help="Dedicated Hugging Face hub cache for this reproduction")
    parser.add_argument("--checkpoint", type=Path,
                        help="Use an already downloaded large/classifier.pt")
    args = parser.parse_args()
    repo_root = Path(__file__).resolve().parents[1]
    manifest = repo_root / "solutions" / "r1" / "checkpoint_manifest.json"
    spec = json.loads(manifest.read_text(encoding="utf-8"))["kumo"]
    repo = args.cache_dir / ("models--" + spec["repo"].replace("/", "--"))
    snapshot = repo / "snapshots" / spec["revision"] / spec["filename"]
    ref = repo / "refs" / "main"

    # The original submission requests the prefetched local main snapshot and
    # verifies its digest. Give that name to the immutable revision in this
    # dedicated cache. Leave an already assigned main in another cache alone.
    if ref.exists() and ref.read_text(encoding="ascii").strip() != spec["revision"]:
        parser.error("This cache already tracks another revision. Choose a fresh --cache-dir.")
    snapshot.parent.mkdir(parents=True, exist_ok=True)
    if snapshot.is_file():
        verify(snapshot, spec)
    else:
        url = f"https://huggingface.co/{spec['repo']}/resolve/{spec['revision']}/{spec['filename']}"
        with tempfile.NamedTemporaryFile(dir=snapshot.parent, delete=False) as output:
            temporary = Path(output.name)
        try:
            source = (args.checkpoint.open("rb") if args.checkpoint
                      else urllib.request.urlopen(url, timeout=180))
            with source, temporary.open("wb") as output:
                shutil.copyfileobj(source, output, length=1024 * 1024)
            verify(temporary, spec)
            os.replace(temporary, snapshot)
        finally:
            temporary.unlink(missing_ok=True)
    ref.parent.mkdir(parents=True, exist_ok=True)
    if not ref.exists():
        with tempfile.NamedTemporaryFile(dir=ref.parent, delete=False) as output:
            temporary = Path(output.name)
            output.write(spec["revision"].encode("ascii"))
        try:
            try:
                os.link(temporary, ref)
            except FileExistsError:
                if ref.read_text(encoding="ascii").strip() != spec["revision"]:
                    raise ValueError("A different revision was assigned to this cache concurrently.")
        finally:
            temporary.unlink(missing_ok=True)
    print(f"Verified {spec['sha256']}  {snapshot}")
    print(f"Set HF_HUB_CACHE to {args.cache_dir.resolve()} for offline checks.")


def verify(path, spec):
    if path.stat().st_size != spec["bytes"]:
        raise ValueError(f"Checkpoint size mismatch at {path}")
    with path.open("rb") as stream:
        digest = hashlib.file_digest(stream, "sha256").hexdigest()
    if digest != spec["sha256"]:
        raise ValueError(f"Checkpoint SHA256 mismatch at {path}: {digest}")


if __name__ == "__main__":
    main()
