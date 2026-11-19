#!/usr/bin/env python3
"""Build a deterministic submission ZIP from verified release source bytes."""
import argparse
import json
import os
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
from _release import digest, public_archive_bytes, solution_id, solution_name


def write_archive(path: Path, archive: bytes) -> bool:
    """Atomically create an archive; return False for an identical existing file."""
    if path.is_symlink():
        raise ValueError("Refusing a symbolic-link output")
    if path.exists():
        if path.is_file() and path.read_bytes() == archive:
            return False
        raise ValueError("Output exists with different contents; choose a new filename")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", dir=path.parent, prefix=".submission-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(archive)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            # Windows rename refuses replacement; POSIX hard linking gives the
            # same exclusive publication without exposing a partially written ZIP.
            if os.name == "nt":
                os.rename(temporary, path)
            else:
                os.link(temporary, path)
        except FileExistsError:
            if not path.is_symlink() and path.is_file() and path.read_bytes() == archive:
                return False
            raise ValueError("Output appeared with different contents; choose a new filename")
        return True
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("solution", type=solution_id, metavar="{submitted,survey-context}")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--external-data", type=Path, help="Prepared tables for the survey-context variant")
    parser.add_argument("--json", action="store_true", help="Print a detailed machine-readable build receipt")
    args = parser.parse_args()
    try:
        if args.solution == "r1" and args.external_data is not None:
            raise ValueError("The submitted model does not use external data")
        archive = public_archive_bytes(args.solution, args.external_data)
        created = write_archive(args.output, archive)
        if args.json:
            print(json.dumps({"solution": args.solution, "name": solution_name(args.solution), "output": str(args.output), "bytes": len(archive), "sha256": digest(archive), "created": created, "historical_archive_reproduced": False}))
        else:
            print(f"{'Built' if created else 'Verified existing'} {solution_name(args.solution)} package: {args.output}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
