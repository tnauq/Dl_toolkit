"""Manual height corrections, batched.

Boxes named here are moved in z to a stated target. This is the list for
lift faults found by eye in the viewer: things roofs.py carried up that
should not have moved, and things it left behind that should have.

Each entry records the height the box is expected to be at BEFORE the fix.
A box that is not at that height is skipped, not moved, so a rerun is a
no-op and an upstream change is reported rather than silently compounded.

Run LAST in the pipeline, after remove.py.
"""
import json

TOL = 1.0  # a box must be within this of `was` to be moved

# name: (was, now)  -- both are origin z
FIXES = {
    # Tree canopy near T spawn, 2026-08-16. The trunk (angled-wall_488..506)
    # is a stack of 53 x 53 x 40 blocks based at 213.4, the main floor.
    # roofs.py read the stack as a wall, doubled it, and carried the canopy
    # resting on it up by one datum of 213.4. ramp-slab_503 took the lift
    # twice. Lowered back onto the trunk top at 693.5.
    'ramp-slab_499': (880.8, 667.4),
    'ramp-slab_501': (890.0, 676.6),
    'ramp-slab_503': (1129.6, 702.8),
    'ramp-slab_507': (890.3, 676.9),
    'ramp-slab_510': (890.3, 676.9),
    'ramp-slab_512': (892.0, 678.6),
    'ramp-slab_515': (893.8, 680.4),
    'ramp-slab_526': (891.3, 677.9),
    'ramp-slab_529': (868.8, 655.4),
    'ramp-slab_531': (889.0, 675.6),
    'ramp-slab_534': (892.0, 678.6),
    'ramp-slab_538': (859.2, 645.8),
    'ramp-slab_539': (843.7, 630.3),
    'ramp-slab_540': (888.5, 675.1),
    'ramp-slab_541': (855.2, 641.8),
    'ramp-slab_542': (890.7, 677.3),
    'ramp-slab_543': (871.2, 657.8),
    'ramp-slab_544': (858.0, 644.6),
    'shallow_504': (922.0, 708.6),
    'shallow_521': (922.3, 708.9),
    'shallow_525': (922.7, 709.3),
    'shallow_532': (921.1, 707.7),

    # Gantry crossbeams, 2026-08-16. Four identical 320 x 53 x 40 beams
    # spanning the walls axis_192 and axis_195, in a row along y at
    # y = 1293.6, 1480.3, 1653.7, 1827.0. axis_348 sits at 713.5; the other
    # three sit 186.7 lower, which is 112 CS x 1.667, so they missed a
    # doubling the fourth received. Raised to match axis_348. Both walls run
    # z 0.1 to 1280.3 and their y spans cover all four beams, so nothing is
    # left behind by the move.
    'axis_345': (526.8, 713.5),
    'axis_346': (526.8, 713.5),
    'axis_347': (526.8, 713.5),

    # Roof panels, 2026-08-16. axis_761, axis_764 and axis_766 are three
    # 40 thick panels tiling side by side in x from -2134 to -960, over the
    # same bay. axis_764 sits at 700.2; the other two sit 213.4 lower, which
    # is exactly one main floor datum, so they missed a lift axis_764
    # received. Raised to match. The walls carrying them (axis_729, _730,
    # _732, _738, _744) top out at 1067.0, so the higher position still
    # clears nothing.
    'axis_761': (486.8, 700.2),
    'axis_766': (486.8, 700.2),

    # Connecting roof panel, 2026-08-16. axis_762 spans exactly the run
    # between axis_761's north edge and axis_734's south face, so it is the
    # panel that joins them. axis_734 tops out at 640.1 and the raised
    # axis_761 starts at 680.2, a gap of 40.1 against a panel 40.0 thick.
    # Raised to sit in that gap, flush to both. Depends on the axis_761 lift
    # above, so it must not be applied on its own.
    'axis_762': (486.8, 660.2),

    # Roof panel continuation, 2026-08-16. axis_765 butts onto axis_764's
    # north edge at y 3174 with the same 40 thickness, so it takes the same
    # lift and the two end up flush.
    'axis_765': (486.8, 700.2),

    # Step panel, 2026-08-16. axis_767 sits edge to edge in x between
    # axis_766 and axis_769, so the gap is a vertical step at each seam
    # rather than a slot. axis_769 tops out at 653.5 and axis_766 starts at
    # 680.2, a span of 26.7 against a panel 40 thick, so it cannot be flush
    # with both. Centred instead: 646.9 to 686.9, overlapping each
    # neighbour by 6.6 and sealing both seams. Overlap blocks rather than
    # opens. Depends on the axis_766 lift above.
    'axis_767': (486.8, 666.9),

    # Ramp landing, 2026-08-16. axis_42 is a 26.7 thick plate that sat at
    # 760.1 with nothing under it, one of the five plates the handoff lists
    # as reachable from neither side. ramp-slab_26 has yaw -90 and pitch
    # 15.64, so once the yaw is applied its footprint is x 3200.7 to 3734.1
    # and y 4450.6 to 5139.0, reaching 401.1 at its high edge to the north.
    # axis_42 starts at y 5121.1, so the two already overlap by 17.9.
    # Lowered so the plate top sits at 401.1 and the ramp runs onto it.
    'axis_42': (760.1, 387.8),

    # Floor panel, 2026-08-16. axis_63 sits edge to edge in x with axis_41
    # at the same 26.7 thickness, one datum of 213.4 above it. Lowered to
    # match, which makes the two continuous. The crates axis_54 and yaw_55
    # already rest on axis_41's top at 346.8, so that is the floor level.
    # Second of the five plates the handoff lists as dead geometry to come
    # back into use. axis_62 butts onto axis_63's west edge, same thickness,
    # also still at 546.8, and is likely the third panel of the same floor.
    'axis_63': (546.8, 333.4),

    # Floor panel, 2026-08-16. axis_62 butts onto axis_63's west edge at
    # x 2347, same 26.7 thickness, same 213.4 datum above it. Third panel of
    # the same floor, lowered to match. Third of the five plates the handoff
    # lists as dead geometry to come back into use.
    'axis_62': (546.8, 333.4),
}

p = json.load(open('dust2_half.json'))
by_name = {b['name']: b for b in p['boxes']}

moved, skipped, missing = [], [], []
for name, (was, now) in FIXES.items():
    box = by_name.get(name)
    if box is None:
        missing.append(name)
        continue
    z = box['origin'][2]
    if abs(z - was) > TOL:
        skipped.append((name, z, was))
        continue
    box['origin'][2] = now
    moved.append(name)

json.dump(p, open('dust2_half.json', 'w'), indent=1)

print(f'moved {len(moved)} of {len(FIXES)} listed')
for name, z, was in skipped:
    print(f'  skipped {name}: z={z}, expected {was}')
for name in missing:
    print(f'  NOT FOUND (already gone or renamed): {name}')
