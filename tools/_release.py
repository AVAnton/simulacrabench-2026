"""Shared, standard-library-only release verification and ZIP construction."""
from __future__ import annotations

import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import zipfile

REPO = Path(__file__).resolve().parents[1]
MODIFIED_FILE = "vendor/sdm/models/base.py"
MODIFICATION_NOTICE = b"# Modified for this submission: cache offload is conditional on _offload_cache.\n"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def manifest(solution: str) -> dict:
    if solution not in ("r1", "v4"):
        raise ValueError("solution must be r1 or v4")
    result = json.loads((REPO / "solutions" / solution / "release_manifest.json").read_text(encoding="utf-8"))
    names = []
    for row in result["entries"]:
        name = row["name"]
        p = PurePosixPath(name)
        if p.is_absolute() or ".." in p.parts or "\\" in name or not name:
            raise ValueError(f"Unsafe manifest member: {name!r}")
        names.append(name)
    if len(names) != len(set(names)):
        raise ValueError("Duplicate manifest members")
    return result


def source_bytes(solution: str, row: dict, external_data: Path | None = None) -> bytes:
    if row["source"] == "external_data":
        if external_data is None:
            raise ValueError("v4 requires six locally prepared CSVs; pass --external-data DIR (see data/README.md)")
        path = external_data / PurePosixPath(row["name"]).name
        expected = row["sha256"]
    else:
        path = REPO / "solutions" / solution / row["name"]
        expected = row["release_sha256"]
    if not path.is_file() or path.is_symlink():
        raise ValueError(f"Missing regular source file: {path}")
    data = path.read_bytes()
    if digest(data) != expected:
        raise ValueError(f"Source SHA256 mismatch: {row['name']}")
    return data


def historical_r1_bytes() -> bytes:
    """Reconstruct in memory ONLY; do not publish the legacy, unnoted source ZIP."""
    meta = manifest("r1")
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=meta["compression_level"]) as z:
        z.comment = bytes.fromhex(meta["archive_comment_hex"])
        for row in meta["entries"]:
            data = source_bytes("r1", row)
            if row["name"] == MODIFIED_FILE:
                if not data.startswith(MODIFICATION_NOTICE):
                    raise ValueError("Expected explicit source modification notice is missing")
                data = data[len(MODIFICATION_NOTICE):]
            if digest(data) != row["sha256"]:
                raise ValueError(f"Historical source SHA256 mismatch: {row['name']}")
            info = zipfile.ZipInfo(row["name"], tuple(row["date_time"]))
            for key in ("compress_type", "create_system", "create_version", "extract_version", "flag_bits", "volume", "internal_attr", "external_attr"):
                setattr(info, key, row[key])
            info.extra = bytes.fromhex(row["extra_hex"])
            info.comment = bytes.fromhex(row["comment_hex"])
            z.writestr(info, data, compress_type=row["compress_type"], compresslevel=meta["compression_level"])
    result = target.getvalue()
    if digest(result) != meta["historical_archive_sha256"]:
        raise ValueError("Original source bytes match, but ZIP SHA256 differs (possibly the local zlib version); no historical archive is written")
    return result


def public_archive_bytes(solution: str, external_data: Path | None = None) -> bytes:
    meta = manifest(solution)
    contents = {row["name"]: source_bytes(solution, row, external_data) for row in meta["entries"]}
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        path = REPO / name
        if not path.is_file():
            raise ValueError(f"Release notice is missing: {name}")
        contents[name] = path.read_bytes()
    provenance = {
        "solution": solution,
        "historical_archive_sha256": meta["historical_archive_sha256"],
        "historical_archive_reproduced": False,
        "changes": ["Prominent modification notice added to vendor/sdm/models/base.py", "Public license and provenance included", "ZIP metadata normalized; ZIP_STORED avoids compression-library differences"],
        "prediction_logic_changed": False,
    }
    if solution == "v4":
        provenance["changes"].append("External-data manifest sanitized to remove private audit controls and original local path layout")
        provenance["external_csvs"] = "Supplied locally and checked against historical hashes; redistribution terms must be reviewed separately"
    contents["PUBLIC_RELEASE.json"] = (json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode()
    target = io.BytesIO()
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_STORED) as z:
        for name, data in sorted(contents.items()):
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            info.compress_type = zipfile.ZIP_STORED
            z.writestr(info, data)
    return target.getvalue()
