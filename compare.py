#!/usr/bin/env python3
"""Compare a dl-mkfixture manifest against a dl-extract index.

Exists to answer one question the docs cannot: does PackageEntry.CRC32 mean
the CRC32 of the file contents? dl-diff's design depends on yes.
"""
import json, sys

manifest = json.load(open(sys.argv[1]))["data"]["entries"]
index = json.load(open(sys.argv[2]))["data"]["entries"]

exp = {e["path"]: e for e in manifest}
got = {e["path"]: e for e in index}

fail = []

missing = sorted(set(exp) - set(got))
extra = sorted(set(got) - set(exp))
if missing:
    fail.append(f"missing from index: {missing}")
if extra:
    fail.append(f"unexpected in index: {extra}")

for path in sorted(set(exp) & set(got)):
    a, b = exp[path], got[path]
    if a["length"] != b["length"]:
        fail.append(f"{path}: length {a['length']} written, {b['length']} read")
    if a["crc32"] != b["crc32"]:
        fail.append(
            f"{path}: crc32 {a['crc32']:#010x} computed, {b['crc32']:#010x} reported"
        )

if fail:
    for f in fail:
        print(f"::error::{f}")
    sys.exit(1)

print(f"round-trip ok — {len(exp)} entries, paths, lengths and CRC32 all agree")
