#!/usr/bin/env python3
"""Call an extracted submission on a user-supplied public/synthetic CSV frame and JSON schema."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--submission-dir", type=Path, required=True, help="Directory extracted from a built ZIP; main.py must be at its root")
    parser.add_argument("--frame", type=Path, required=True, help="CSV in the organizer frame format, including TRAIN/QUERY rows")
    parser.add_argument("--schema", type=Path, required=True, help="Matching organizer JSON schema")
    parser.add_argument("--output", type=Path, required=True, help="New JSON file for the returned probability vectors")
    parser.add_argument("--hf-cache", type=Path, required=True)
    device = parser.add_mutually_exclusive_group()
    device.add_argument("--gpu", help="Optional CUDA device index or GPU UUID; omission preserves the scheduler's CUDA_VISIBLE_DEVICES")
    device.add_argument("--cpu", action="store_true", help="Hide CUDA devices and run on CPU (slower; competition resource claims do not apply)")
    args = parser.parse_args()
    try:
        if args.output.exists():
            raise ValueError("Output exists; choose a new filename")
        os.environ.update(HF_HUB_CACHE=str(args.hf_cache.resolve()), HF_HUB_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
        if args.gpu is not None:
            os.environ["CUDA_VISIBLE_DEVICES"] = args.gpu
        elif args.cpu:
            os.environ["CUDA_VISIBLE_DEVICES"] = ""
        sys.dont_write_bytecode = True
        import pandas as pd
        frame = pd.read_csv(args.frame, dtype=str, keep_default_na=False, na_values=[""])
        schema = json.loads(args.schema.read_text(encoding="utf-8"))
        path = args.submission_dir.resolve()
        if not (path / "main.py").is_file():
            raise ValueError("main.py must exist directly inside --submission-dir")
        sys.path.insert(0, str(path))
        spec = importlib.util.spec_from_file_location("submission_main", path / "main.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        result = module.predict(frame, schema)
        output = json.dumps(result, default=lambda x: x.tolist(), allow_nan=False)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(output + "\n")
        print(f"Wrote predictions to {args.output}")
        return 0
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
