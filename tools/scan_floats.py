#!/usr/bin/env python3
"""
scan_floats.py — corpus sweep for float literals VRF's reserializer would round.

VRF writes floats to 6 decimal places. Any source literal carrying MORE than 6
decimals is a value dl-patch would silently alter on a parse-and-reserialize
round trip, even in keys the caller never asked to change. This script finds
them. It reads only; it never writes into the corpus.

    python3 tools/scan_floats.py --root <dir> [--dp 6] [--json out.json]

Exit codes (Deadlock.Contracts convention):
    0  scan completed, NO literals over the threshold
    1  scan completed, literals over the threshold WERE found
    2  misuse (bad arguments)
    3  missing dependency / root does not exist

Deterministic: files are walked in sorted order, findings are emitted in
(file, line, column) order, so two runs over the same tree byte-match.
"""

import argparse
import json
import os
import re
import sys

# A KV3 float literal. Requires a digit before and after the point so that
# version guids, ranges and dotted paths do not register. The fractional part
# is captured on its own so its length is the precision measure.
FLOAT_RE = re.compile(rb"(?<![\w.])(-?\d+)\.(\d+)(?![\w.])")

# Lines carrying these are structural, not numeric data. KV3 headers embed
# version guids that can look numeric to a permissive regex.
SKIP_LINE = re.compile(rb"<!--|kv3\s+encoding:|resource_name:")

DEFAULT_DP = 6
MAX_REPORTED = 200


def scan_file(path, dp):
    """Return a list of findings for one file. Never raises on bad bytes."""
    out = []
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError as e:
        return [{"file": path, "line": 0, "col": 0, "literal": "",
                 "decimals": 0, "error": str(e)}]

    for lineno, raw in enumerate(data.split(b"\n"), 1):
        if SKIP_LINE.search(raw):
            continue
        for m in FLOAT_RE.finditer(raw):
            frac = m.group(2)
            if len(frac) <= dp:
                continue
            literal = m.group(0).decode("utf-8", "replace")
            out.append({
                "file": path,
                "line": lineno,
                "col": m.start() + 1,
                "literal": literal,
                "decimals": len(frac),
                "rounded": ("%%.%df" % dp) % float(literal),
            })
    return out


def walk(root, exts):
    """Yield matching file paths in deterministic order."""
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames):
            if any(name.endswith(e) for e in exts):
                yield os.path.join(dirpath, name)


def main():
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--root", required=True,
                    help="directory to scan (a GameTracking-Deadlock checkout)")
    ap.add_argument("--dp", type=int, default=DEFAULT_DP,
                    help="decimal places VRF preserves (default 6)")
    ap.add_argument("--ext", default=".vdata",
                    help="comma-separated extensions to scan (default .vdata)")
    ap.add_argument("--json", dest="json_out", default=None,
                    help="write the full finding list here")
    try:
        args = ap.parse_args()
    except SystemExit:
        return 2

    if not os.path.isdir(args.root):
        print("root does not exist: %s" % args.root, file=sys.stderr)
        return 3

    exts = tuple(e if e.startswith(".") else "." + e
                 for e in args.ext.split(",") if e)

    files = list(walk(args.root, exts))
    if not files:
        print("no files matching %s under %s" % (",".join(exts), args.root),
              file=sys.stderr)
        return 3

    findings = []
    for path in files:
        findings.extend(scan_file(path, args.dp))

    by_file = {}
    for f in findings:
        by_file.setdefault(f["file"], 0)
        by_file[f["file"]] += 1

    result = {
        "root": args.root,
        "extensions": list(exts),
        "decimal_places_preserved": args.dp,
        "files_scanned": len(files),
        "files_with_findings": len(by_file),
        "findings_total": len(findings),
        "worst_precision": max((f["decimals"] for f in findings), default=0),
        "files": [{"file": k, "count": by_file[k]} for k in sorted(by_file)],
        "findings": findings[:MAX_REPORTED],
        "findings_truncated": len(findings) > MAX_REPORTED,
    }

    if args.json_out:
        os.makedirs(os.path.dirname(args.json_out) or ".", exist_ok=True)
        with open(args.json_out, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, sort_keys=False)
            f.write("\n")

    # human summary to stderr, machine result to stdout
    print("[scan] %d files, %d over %d dp, in %d files (worst %d dp)"
          % (len(files), len(findings), args.dp, len(by_file),
             result["worst_precision"]), file=sys.stderr)
    for f in findings[:20]:
        print("  %s:%d  %s -> %s"
              % (os.path.relpath(f["file"], args.root), f["line"],
                 f.get("literal"), f.get("rounded")), file=sys.stderr)
    if len(findings) > 20:
        print("  ... %d more" % (len(findings) - 20), file=sys.stderr)

    json.dump(result, sys.stdout, indent=2)
    sys.stdout.write("\n")

    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
