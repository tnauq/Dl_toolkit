#!/usr/bin/env python3
"""repo_dump.py - emit a single artifact describing the whole repo.

Produces two files under out/:

  repo-manifest.md   every tracked file: path, size, lines, sha1, plus a
                     tree, a language breakdown, and a list of what got
                     skipped and why. Read this first.
  repo-dump.md       the full text of every source file, fenced, in tree
                     order. This is the one to hand to someone who needs
                     the whole picture.

WHAT IS INCLUDED
Files git tracks, so nothing generated, nothing ignored, no .git. Text
files are dumped whole up to MAX_BYTES each. Anything binary, anything
over the cap, and anything matching SKIP_GLOBS is listed in the manifest
with its size and hash but not dumped, so the omission is visible rather
than silent.

The big plan JSON is skipped by content on purpose: it is a megabyte of
coordinates that says nothing a census does not, and it would drown the
code. The manifest reports its box count instead.

SIZE
The dump is chunked at CHUNK_BYTES so no single file is unwieldy;
repo-dump.md becomes repo-dump-1.md, -2.md and so on when it needs to.
The manifest is never chunked.

Usage:
  python3 repo_dump.py              # from the repo root
  python3 repo_dump.py --out DIR
"""

import hashlib
import json
import os
import subprocess
import sys

MAX_BYTES = 200_000          # per file, before it is listed not dumped
CHUNK_BYTES = 900_000        # per output part

# Listed in the manifest, never dumped.
SKIP_GLOBS = [
    ".vmap", ".vpk", ".vdata_c", ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".ico", ".zip", ".gz", ".dll", ".exe", ".pdb", ".bin",
]

# Dumped as a summary rather than in full, keyed by suffix of the path.
SUMMARISE = ["docs/plans/dust2_full.json", "docs/plans/dust2_half.json"]

LANG = {
    ".py": "python", ".cs": "csharp", ".js": "javascript", ".ts": "typescript",
    ".html": "html", ".css": "css", ".json": "json", ".yml": "yaml",
    ".yaml": "yaml", ".md": "markdown", ".sh": "bash", ".txt": "",
    ".csproj": "xml", ".sln": "", ".gi": "", ".kv3": "",
}


def git_files():
    try:
        out = subprocess.run(["git", "ls-files", "-z"],
                             capture_output=True, check=True).stdout
        return sorted(p for p in out.decode("utf-8", "replace").split("\0") if p)
    except Exception as exc:
        print("git ls-files failed (%s), walking the tree instead" % exc)
        hits = []
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs
                       if d not in (".git", "node_modules", "bin", "obj")]
            for fn in files:
                hits.append(os.path.relpath(os.path.join(root, fn), "."))
        return sorted(hits)


def is_binary(data):
    if b"\0" in data[:8000]:
        return True
    try:
        data[:8000].decode("utf-8")
    except UnicodeDecodeError:
        return True
    return False


def summarise_plan(path, data):
    try:
        plan = json.loads(data.decode("utf-8"))
    except Exception:
        return "could not parse as JSON"
    boxes = plan.get("boxes", [])
    lines = ["name: %s, version: %s, cell: %s"
             % (plan.get("name"), plan.get("version"), plan.get("cell")),
             "boxes: %d" % len(boxes)]
    mats = {}
    rot = 0
    lo = [9e9] * 3
    hi = [-9e9] * 3
    for b in boxes:
        mats[b.get("material")] = mats.get(b.get("material"), 0) + 1
        a = b.get("angles") or [0, 0, 0]
        if any(a):
            rot += 1
        o = b["origin"]
        e = b["extents"]
        for i in range(3):
            lo[i] = min(lo[i], o[i] - e[i] / 2)
            hi[i] = max(hi[i], o[i] + e[i] / 2)
    lines.append("rotated boxes: %d" % rot)
    lines.append("m_ twins: %d"
                 % sum(1 for b in boxes if b["name"].startswith("m_")))
    lines.append("aabb min (ignoring rotation): %s"
                 % [round(v, 2) for v in lo])
    lines.append("aabb max (ignoring rotation): %s"
                 % [round(v, 2) for v in hi])
    for m, n in sorted(mats.items(), key=lambda kv: -kv[1]):
        lines.append("material %s: %d" % (m, n))
    for e in plan.get("entities", []):
        lines.append("entity %s at %s props %s"
                     % (e.get("classname"), e.get("origin"),
                        e.get("properties")))
    lines.append("")
    lines.append("first 5 box names: %s"
                 % ", ".join(b["name"] for b in boxes[:5]))
    return "\n".join(lines)


def main():
    outdir = "out"
    if "--out" in sys.argv:
        outdir = sys.argv[sys.argv.index("--out") + 1]
    os.makedirs(outdir, exist_ok=True)

    files = git_files()
    records = []

    for path in files:
        if not os.path.isfile(path):
            continue
        with open(path, "rb") as f:
            data = f.read()
        sha = hashlib.sha1(data).hexdigest()[:12]
        ext = os.path.splitext(path)[1].lower()

        reason = None
        if ext in SKIP_GLOBS:
            reason = "binary or bulk type"
        elif any(path.endswith(s) for s in SUMMARISE):
            reason = "summarised"
        elif is_binary(data):
            reason = "binary content"
        elif len(data) > MAX_BYTES:
            reason = "over %d bytes" % MAX_BYTES

        text = None
        if reason is None:
            text = data.decode("utf-8", "replace")
        elif reason == "summarised":
            text = summarise_plan(path, data)

        records.append({
            "path": path, "size": len(data), "sha": sha, "ext": ext,
            "reason": reason, "text": text,
            "lines": (text.count("\n") + 1) if text else 0,
        })

    # ---- manifest ----
    man = []
    man.append("# Repo manifest\n")
    man.append("%d tracked files, %d bytes total.\n"
               % (len(records), sum(r["size"] for r in records)))

    man.append("\n## Tree\n\n```\n")
    seen = set()
    for r in records:
        parts = r["path"].split("/")
        for i in range(len(parts) - 1):
            d = "/".join(parts[:i + 1])
            if d not in seen:
                seen.add(d)
                man.append("%s%s/\n" % ("  " * i, parts[i]))
        man.append("%s%s  (%d B, %d lines)\n"
                   % ("  " * (len(parts) - 1), parts[-1], r["size"], r["lines"]))
    man.append("```\n")

    by_ext = {}
    for r in records:
        e = r["ext"] or "(none)"
        d = by_ext.setdefault(e, [0, 0, 0])
        d[0] += 1
        d[1] += r["size"]
        d[2] += r["lines"]
    man.append("\n## By type\n\n| ext | files | bytes | lines |\n|---|---|---|---|\n")
    for e, d in sorted(by_ext.items(), key=lambda kv: -kv[1][1]):
        man.append("| %s | %d | %d | %d |\n" % (e, d[0], d[1], d[2]))

    skipped = [r for r in records if r["reason"] and r["reason"] != "summarised"]
    man.append("\n## Not dumped (%d)\n\n| path | bytes | sha1 | why |\n|---|---|---|---|\n"
               % len(skipped))
    for r in skipped:
        man.append("| %s | %d | %s | %s |\n"
                   % (r["path"], r["size"], r["sha"], r["reason"]))

    man.append("\n## All files\n\n| path | bytes | lines | sha1 |\n|---|---|---|---|\n")
    for r in records:
        man.append("| %s | %d | %d | %s |\n"
                   % (r["path"], r["size"], r["lines"], r["sha"]))

    with open(os.path.join(outdir, "repo-manifest.md"), "w") as f:
        f.write("".join(man))

    # ---- dump, chunked ----
    parts = []
    cur = ["# Repo dump, part 1\n\nEvery tracked text file in tree order. "
           "See repo-manifest.md for what was left out.\n"]
    size = 0
    for r in records:
        if r["text"] is None:
            continue
        lang = LANG.get(r["ext"], "")
        head = ("\n\n---\n\n## `%s`\n\n%s%d bytes, %d lines, sha1 %s\n\n```%s\n"
                % (r["path"],
                   "SUMMARY ONLY, full file not dumped. " if r["reason"] else "",
                   r["size"], r["lines"], r["sha"], lang))
        body = r["text"]
        if not body.endswith("\n"):
            body += "\n"
        block = head + body + "```\n"
        if size + len(block) > CHUNK_BYTES and size:
            parts.append("".join(cur))
            cur = ["# Repo dump, part %d\n" % (len(parts) + 1)]
            size = 0
        cur.append(block)
        size += len(block)
    parts.append("".join(cur))

    names = []
    for i, p in enumerate(parts, 1):
        n = ("repo-dump.md" if len(parts) == 1 else "repo-dump-%d.md" % i)
        with open(os.path.join(outdir, n), "w") as f:
            f.write(p)
        names.append(n)

    print("wrote %s/repo-manifest.md" % outdir)
    for n in names:
        print("wrote %s/%s (%d bytes)"
              % (outdir, n, os.path.getsize(os.path.join(outdir, n))))
    print("%d files, %d dumped, %d listed only"
          % (len(records),
             sum(1 for r in records if r["text"] is not None),
             len(skipped)))


if __name__ == "__main__":
    main()
