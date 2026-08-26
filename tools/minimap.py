#!/usr/bin/env python3
"""minimap.py - top-down PNG of the plan, marked up to the in-game legend.

    python3 tools/minimap.py [docs/plans/dust2_full.json] [out.png]

WHAT IT DRAWS. Every box, projected straight down and shaded by the height of
its top face, so the map reads as floors rather than a silhouette. Lane
polylines over that. Then one marker per legend entry, placed from the
entities the plan actually contains.

THE LEGEND MAPPING IS THE WHOLE PROBLEM, and it is only as good as the
classnames below. Where the game's legend word and the plan's classname
differ, this file uses the plan and says so:

    legend         drawn from
    Patron         nothing - ABSENT from the plan, never surveyed
    Titan          nothing - ABSENT
    Base Guard     nothing - ABSENT
    Guardian       npc_boss_tier3   (batch13's own word for these)
    Walker         npc_boss_tier2
    Rejuvenator    the midboss camp, subclass neutral_camp_midboss
    Soul Urn       citadel_trigger_idol_return
    Sinner's       the vault camps, subclass neutral_camp_vaults
    Power-up       citadel_item_powerup_spawner
    Shop           trigger_item_shop
    Teleporter     nothing yet - held back, classname unknown
    Camps T1/2/3   neutral_camp_weak / _medium / _strong

Note the Guardian/Walker pairing follows batch13, where npc_boss_tier3 is the
guardian and npc_boss_tier2 the walker. If the game means the opposite, the
two swap here and nowhere else.

Amber and Sapphire come from `teamnumber`: batch13 uses TEAM_A for the
authored half and flips it on the mirror, so team is read per entity rather
than by which side of the map something is on.

Absent legend entries are LISTED IN THE MARGIN rather than dropped silently,
because a minimap that quietly omits the patron looks finished when it is not.
"""

import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt              # noqa: E402
from matplotlib.patches import Polygon       # noqa: E402

# Legend colours, eyeballed off the in-game legend.
AMBER = "#f0a02a"
SAPPHIRE = "#2f7ef0"
NEUTRAL = "#c8b88a"
CAMP = "#4fbf9f"
TEAL = "#5fd3d0"
GOLD = "#f2c744"
SHOP = "#5fd07a"
LANE = "#8899aa"

TEAM_AMBER = "2"     # batch13's TEAM_A

# Anything with its top above this is drawn see-through. INVENTED: it sits
# just over the sky bridge deck at 1280 so the bridge itself stays solid and
# the hexagon room above it does not.
UPPER_Z = 1330.0


def rot2(x, y, deg):
    a = math.radians(deg)
    c, s = math.cos(a), math.sin(a)
    return x * c - y * s, x * s + y * c


def box_corners(b):
    o, e = b["origin"], b["extents"]
    yaw = b.get("angles", [0, 0, 0])[1]
    hx, hy = e[0] / 2.0, e[1] / 2.0
    pts = []
    for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
        dx, dy = rot2(sx * hx, sy * hy, yaw)
        pts.append((o[0] + dx, o[1] + dy))
    return pts


def ents(plan, cls):
    return [e for e in plan.get("entities", []) if e.get("classname") == cls]


def camps(plan, subclass):
    return [e for e in ents(plan, "info_neutral_trooper_camp")
            if (e.get("properties") or {}).get("subclass_name") == subclass]


def team_colour(e):
    t = (e.get("properties") or {}).get("teamnumber", "")
    if t == TEAM_AMBER:
        return AMBER
    if t:
        return SAPPHIRE
    return NEUTRAL


def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "docs/plans/dust2_full.json"
    out = sys.argv[2] if len(sys.argv) > 2 else "minimap.png"
    with open(path) as f:
        plan = json.load(f)

    boxes = plan["boxes"]
    zs = [b["origin"][2] + b["extents"][2] / 2.0 for b in boxes]
    zlo, zhi = min(zs), max(zs)

    fig, ax = plt.subplots(figsize=(13, 13), dpi=140)
    fig.patch.set_facecolor("#0d1117")
    ax.set_facecolor("#0d1117")

    # Floors first, painted low to high so an upper deck sits on top of what
    # is under it. Height drives the shade: without that the map is one flat
    # blob and the bridge disappears into the ground.
    cmap = plt.get_cmap("bone")
    for b in sorted(boxes, key=lambda q: q["origin"][2] + q["extents"][2] / 2.0):
        top = b["origin"][2] + b["extents"][2] / 2.0
        t = (top - zlo) / max(1.0, zhi - zlo)
        # Upper decks go translucent. Painted solid, the hexagon room's roof
        # at z 2587 is both the highest and therefore the brightest thing on
        # the map, and it blanks out the whole middle - the sky bridge, the
        # mid lane and the shops under it. Fading with height keeps the
        # stacking readable in both directions.
        a = 1.0 if top < UPPER_Z else 0.42
        ax.add_patch(Polygon(box_corners(b), closed=True,
                             facecolor=cmap(0.18 + 0.72 * t), alpha=a,
                             edgecolor="none", zorder=1 + t))

    for p in plan.get("paths", []):
        pts = [n["origin"] for n in p.get("nodes", []) if "origin" in n]
        if len(pts) > 1:
            ax.plot([q[0] for q in pts], [q[1] for q in pts],
                    color=LANE, lw=1.0, alpha=0.55, zorder=5)

    def mark(items, marker, size, colour, label, edge="#0d1117"):
        if not items:
            return None
        xs = [e["origin"][0] for e in items]
        ys = [e["origin"][1] for e in items]
        cs = colour if isinstance(colour, str) else [colour(e) for e in items]
        ax.scatter(xs, ys, marker=marker, s=size, c=cs, edgecolors=edge,
                   linewidths=0.7, zorder=10, label="%s (%d)"
                   % (label, len(items)))
        return True

    missing = []
    # bosses
    mark(ents(plan, "npc_boss_tier3"), "D", 90, team_colour, "Guardian")
    mark(ents(plan, "npc_boss_tier2"), "D", 70, team_colour, "Walker")
    for word, cls in (("Patron", "npc_patron"),
                      ("Titan", "npc_titan"),
                      ("Base Guard", "npc_base_guard")):
        if not ents(plan, cls):
            missing.append(word)

    # objectives and pickups
    mark(camps(plan, "neutral_camp_midboss"), "*", 320, GOLD, "Rejuvenator")
    mark(ents(plan, "citadel_trigger_idol_return"), "o", 90, TEAL, "Soul Urn")
    mark(camps(plan, "neutral_camp_vaults"), "s", 60, NEUTRAL, "Sinner's")
    mark(ents(plan, "citadel_item_powerup_spawner"), "o", 110, GOLD,
         "Power-up")
    mark(ents(plan, "trigger_item_shop"), "P", 110, SHOP, "Shop")

    # camps, by tier
    for sub, size, word in (("neutral_camp_weak", 45, "Camp T1"),
                            ("neutral_camp_medium", 75, "Camp T2"),
                            ("neutral_camp_strong", 110, "Camp T3")):
        mark(camps(plan, sub), "^", size, CAMP, word)

    # things the plan cannot draw yet
    tele = [e for e in plan.get("entities", [])
            if "teleport" in e.get("classname", "")]
    if tele:
        mark(tele, "X", 110, "#cfd6e0", "Teleporter")
    else:
        missing.append("Teleporter")

    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("dust2 - %d boxes, %d entities"
                 % (len(boxes), len(plan.get("entities", []))),
                 color="#e6edf3", fontsize=13, pad=14)

    leg = ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0),
                    facecolor="#161b22", edgecolor="#30363d",
                    labelcolor="#e6edf3", fontsize=9, framealpha=1.0)
    leg.set_zorder(20)

    if missing:
        # In the margin, not omitted. A minimap missing the patron should say
        # the patron is missing.
        fig.text(0.78, 0.06, "not in the plan:\n  " + "\n  ".join(missing),
                 color="#8b949e", fontsize=9, va="bottom", family="monospace")

    fig.savefig(out, facecolor=fig.get_facecolor(), bbox_inches="tight")
    print("wrote %s  (%d boxes, %d entities)"
          % (out, len(boxes), len(plan.get("entities", []))))
    if missing:
        print("absent from the plan: %s" % ", ".join(missing))


if __name__ == "__main__":
    main()
