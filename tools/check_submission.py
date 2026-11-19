#!/usr/bin/env python3
"""Run a supplied organizer checker on a ZIP (contract smoke test, not hidden-test evaluation)."""
import argparse
import hashlib
import os
from pathlib import Path
import subprocess
import sys

HISTORICAL_CHECKER_SHA256 = "e1f7316642f440ece2aedd6e149f5f0a47c108fc836c602815fdd026aeee3d8f"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--checker", type=Path, required=True, help="Official tools/check_submission_zip.py from the organizer repository")
    parser.add_argument("--checker-sha256", default=HISTORICAL_CHECKER_SHA256, help=argparse.SUPPRESS)
    parser.add_argument("--hf-cache", type=Path, required=True, help="Prepared Hugging Face hub cache, not its parent directory")
    device = parser.add_mutually_exclusive_group()
    device.add_argument("--gpu", help="Optional CUDA device index or GPU UUID; omission preserves the scheduler's CUDA_VISIBLE_DEVICES")
    device.add_argument("--cpu", action="store_true", help="Hide CUDA devices for a CPU smoke check (competition GPU timings do not apply)")
    args = parser.parse_args()
    try:
        if hashlib.sha256(args.checker.read_bytes()).hexdigest() != args.checker_sha256:
            raise ValueError("Checker SHA256 mismatch; inspect the version before specifying a different --checker-sha256")
        if not args.archive.is_file() or not args.hf_cache.is_dir():
            raise ValueError("Archive or prepared cache is missing")
        env = dict(os.environ, HF_HUB_CACHE=str(args.hf_cache.resolve()), HF_HUB_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1", PYTHONDONTWRITEBYTECODE="1")
        if args.gpu is not None:
            env["CUDA_VISIBLE_DEVICES"] = args.gpu
        elif args.cpu:
            env["CUDA_VISIBLE_DEVICES"] = ""
        return subprocess.run([sys.executable, str(args.checker.resolve()), str(args.archive.resolve())], env=env, check=False).returncode
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
