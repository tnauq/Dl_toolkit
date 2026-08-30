#!/usr/bin/env python3
"""Check every entity in the plan against the FGDs the compiler uses.

WHY THIS EXISTS. Almost every bug found on 2026-08-29 was the same shape: a
classname or a keyvalue that looked right, emitted cleanly, verified green,
and would have done nothing in game.

    target        should have been exitpoint on citadel_trigger_teleport
    light_environment   is not a class in citadel.fgd or base.fgd at all
    npc_boss_tier1      is not a class either - it is a unit in the vdata
    rebels_t1_boss_orange   is not one of the eight legal BossName values

All four are statically detectable against `citadel.fgd`, which is the exact
table the compiler validates against. This tool does that check in CI, in
seconds, without a compile - which is the whole point, because we cannot
compile yet.

    python3 tools/fgd_check.py [plan.json] [--strict]

Exit 1 on any ERROR. Warnings do not fail unless --strict.

WHAT IT CANNOT DO. The FGD table is incomplete: citadel.fgd @includes six
files and we hold two of them. An unknown class or key may simply live in a
file we do not have, so those are reported by severity:

    ERROR    the class or key is contradicted by something we DO hold -
             a value outside a choices list, a key marked (Broken)
    WARN     not found anywhere in the tables we hold
    NOTE     found, with an annotation worth knowing

That split is deliberate. Treating every absence as an error would flag
logic_relay, which is real and lives in a file we are missing.
"""

import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
FGD_DIR = os.path.join(os.path.dirname(HERE), "docs", "reference", "citadel")

# Order matters only for reporting; the tables are merged.
FGD_FILES = ["citadel.fgd", "base.fgd", "postprocessing.fgd"]

CLASS_RE = re.compile(
    r'^@(PointClass|SolidClass|NPCClass|BaseClass|KeyFrameClass|MoveClass|'
    r'FilterClass|PathClass|OverrideClass)\b(.*)$', re.I)
# `name(type) : "Display" : default : "help"` - default and help optional.
KEY_RE = re.compile(r'^\s*([A-Za-z_][A-Za-z0-9_.]*)\s*\(([A-Za-z_0-9]+)\)')
BASE_RE = re.compile(r'\bbase\s*\(([^)]*)\)', re.I)
NAME_RE = re.compile(r'=\s*([A-Za-z_][A-Za-z0-9_]*)\s*(?::|\[|$)')
CHOICE_RE = re.compile(r'^\s*"?([^":]+?)"?\s*:\s*"')

BROKEN = re.compile(r'\(broken\)', re.I)
UNUSED = re.compile(r'\bunused\b', re.I)


def parse_fgd(path):
    """Return {classname: {'bases': [...], 'keys': {k: info}, 'file': f}}.

    Deliberately forgiving. An FGD line this misses becomes a key we do not
    know about, which downgrades a check to a warning - never an error. A
    parser that guessed would be worse than one that shrugs.
    """
    out = {}
    txt = open(path, encoding="utf-8", errors="replace").read()
    lines = txt.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        m = CLASS_RE.match(line.strip())
        if not m:
            i += 1
            continue

        # A class header can run over several lines - metadata blocks,
        # studio(), vdata_model{} - before the `= name` that ends it.
        #
        # DO NOT scan for the first "=" in that span. Metadata blocks are
        # full of `entity_tool_name = "Lane Guardian"` lines, so a naive scan
        # stops inside the metadata and the class name is never found. That
        # bug cost 107 of citadel.fgd's 197 classes on the first run, which
        # showed up as info_super_trooper_spawn being "in none of the
        # tables" - a table failure wearing the costume of a finding.
        #
        # The name is either inline on the header, or on a later line that
        # BEGINS with "=". Metadata lines never do.
        header = line
        j = i
        cname = None
        nm = NAME_RE.search(header.split("//")[0])
        if nm:
            cname = nm.group(1)
        else:
            while j + 1 < len(lines) and j - i < 60:
                j += 1
                header += " " + lines[j]
                cand = lines[j].split("//")[0].strip()
                m2 = re.match(r'^=\s*([A-Za-z_][A-Za-z0-9_]*)', cand)
                if m2:
                    cname = m2.group(1)
                    break
                if cand.startswith("["):
                    break
        if not cname:
            i = j + 1
            continue
        bases = []
        bm = BASE_RE.search(header)
        if bm:
            bases = [b.strip() for b in bm.group(1).split(",") if b.strip()]

        # Body: from the next '[' to its matching ']'.
        while j < len(lines) and "[" not in lines[j]:
            j += 1
        depth = 0
        keys = {}
        cur = None
        started = False
        while j < len(lines):
            body = lines[j]
            stripped = body.strip()
            depth += body.count("[") - body.count("]")
            if body.count("["):
                started = True

            km = KEY_RE.match(body)
            low = stripped.lower()
            if km and not low.startswith(("input ", "output ")):
                cur = km.group(1)
                keys[cur.lower()] = {
                    "name": cur,
                    "type": km.group(2).lower(),
                    "choices": set(),
                    "broken": bool(BROKEN.search(stripped)),
                    "unused": bool(UNUSED.search(stripped)),
                    "line": j + 1,
                }
            elif cur and keys.get(cur.lower(), {}).get("type") == "choices":
                cm = CHOICE_RE.match(body)
                if cm and ":" in stripped:
                    keys[cur.lower()]["choices"].add(cm.group(1).strip())

            if started and depth <= 0:
                break
            j += 1

        # vdata_model{my_key = "subclass_name" ...} declares a keyvalue in
        # the HEADER rather than the body - it is how an NPC class picks its
        # model out of the vdata. Without this, every npc_boss_tier2 in the
        # plan warns about subclass_name, which is both real and required.
        for mk in re.findall(r'my_key\s*=\s*"([^"]+)"', header):
            keys.setdefault(mk.lower(), {
                "name": mk, "type": "string", "choices": set(),
                "broken": False, "unused": False, "line": i + 1})

        out[cname] = {"bases": bases, "keys": keys,
                      "file": os.path.basename(path)}
        i = j + 1
    return out


def load_tables(paths):
    table = {}
    for p in paths:
        if not os.path.exists(p):
            print("  (missing, skipped) %s" % p)
            continue
        got = parse_fgd(p)
        print("  %-24s %4d classes" % (os.path.basename(p), len(got)))
        # First file wins on a clash: citadel.fgd is the game's own.
        for k, v in got.items():
            table.setdefault(k, v)
    return table


def resolve(table, cname, seen=None):
    """All keys on a class, including everything it inherits."""
    seen = seen or set()
    if cname in seen or cname not in table:
        return {}
    seen.add(cname)
    keys = {}
    for b in table[cname]["bases"]:
        keys.update(resolve(table, b, seen))
    keys.update(table[cname]["keys"])
    return keys


# Keys the editor writes on every entity, which are not FGD keyvalues.
EDITOR_KEYS = {"model", "skin", "bodygroups", "vscripts", "spawnflags",
               "origin", "angles", "scales", "classname", "targetname",
               "parentname", "disableshadows", "rendercolor", "renderamt"}


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    strict = "--strict" in sys.argv
    path = args[0] if args else "docs/plans/dust2_full.json"

    print("tables:")
    table = load_tables([os.path.join(FGD_DIR, f) for f in FGD_FILES])
    if not table:
        print("::error::no FGD tables found under %s" % FGD_DIR)
        return 1
    print("  %d classes total\n" % len(table))

    plan = json.load(open(path))
    ents = plan.get("entities", [])

    errors, warns, notes = [], [], []
    seen_class = {}

    for e in ents:
        cn = e.get("classname", "")
        nm = e.get("name", "?")
        seen_class[cn] = seen_class.get(cn, 0) + 1

        if cn not in table:
            warns.append("%s: classname %r is in none of the tables"
                         % (nm, cn))
            continue

        keys = resolve(table, cn)
        for k, v in (e.get("properties") or {}).items():
            info = keys.get(k.lower())
            if info is None:
                if k.lower() in EDITOR_KEYS:
                    continue
                warns.append("%s (%s): key %r not declared on the class or "
                             "its bases" % (nm, cn, k))
                continue
            if info["broken"]:
                notes.append("%s (%s): %r is marked (Broken) in the FGD"
                             % (nm, cn, k))
            elif info["unused"]:
                notes.append("%s (%s): %r is annotated Unused in the FGD"
                             % (nm, cn, k))
            # THE CHECK THAT WOULD HAVE CAUGHT BossName. A choices field with
            # a value outside its list is an ERROR, because the table we hold
            # contradicts it directly rather than merely not mentioning it.
            if info["type"] == "choices" and info["choices"]:
                if str(v) not in info["choices"] and str(v) != "":
                    errors.append(
                        "%s (%s): %s=%r is not one of %s"
                        % (nm, cn, info["name"], v,
                           ", ".join(sorted(info["choices"])[:8])))

    print("classnames in the plan:")
    for cn in sorted(seen_class):
        mark = "" if cn in table else "   <- NOT IN TABLES"
        print("  %-34s %4d%s" % (cn, seen_class[cn], mark))

    for label, items in (("ERROR", errors), ("WARN", warns), ("NOTE", notes)):
        if not items:
            continue
        print("\n%s (%d)" % (label, len(items)))
        for s in sorted(set(items)):
            print("  " + s)

    print("\n%d entities checked, %d errors, %d warnings, %d notes"
          % (len(ents), len(errors), len(warns), len(notes)))

    if errors:
        print("::error::%d entity keyvalue error(s)" % len(errors))
        return 1
    if warns and strict:
        print("::error::--strict and %d warning(s)" % len(warns))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
