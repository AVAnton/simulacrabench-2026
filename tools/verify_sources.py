#!/usr/bin/env python3
"""Verify release sources without importing models, downloading weights or using a GPU."""
import argparse
import ast
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
from _release import digest, historical_r1_bytes, manifest, source_bytes, solution_id, solution_name


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--solution", type=lambda value: value if value == "all" else solution_id(value), metavar="{submitted,survey-context,all}", default="all")
    parser.add_argument("--external-data", type=Path, help="Also verify the locally prepared survey-context tables")
    parser.add_argument("--original-submission", action="store_true", dest="historical_r1", help="Also verify the original submitted package in memory")
    parser.add_argument("--historical-r1", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--json", action="store_true", help="Print detailed machine-readable verification results")
    args = parser.parse_args()
    result = {}
    try:
        for solution in (("r1", "v4") if args.solution == "all" else (args.solution,)):
            verified = 0
            withheld = []
            for row in manifest(solution)["entries"]:
                if row["source"] == "external_data" and args.external_data is None:
                    withheld.append(row["name"])
                    continue
                data = source_bytes(solution, row, args.external_data)
                if row["name"].endswith(".py"):
                    ast.parse(data, filename=row["name"])
                verified += 1
            result[solution] = {"verified_files": verified, "external_data_not_bundled": withheld}
        if args.historical_r1:
            historical = historical_r1_bytes()
            result["historical_r1"] = {"sha256": digest(historical), "bytes": len(historical), "verified_in_memory_only": True}
        if args.json:
            print(json.dumps(result, indent=2))
        else:
            for key, checked in result.items():
                if key == "historical_r1":
                    print("Verified the original submitted package in memory.")
                else:
                    suffix = " (external tables not supplied)" if checked["external_data_not_bundled"] else ""
                    print(f"Verified {solution_name(key)} sources: {checked['verified_files']} files{suffix}.")
        return 0
    except (OSError, ValueError, SyntaxError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
