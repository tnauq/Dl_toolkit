"""Manual height corrections, batched.

Boxes named here are moved in z to a stated target. This is the list for
lift faults found by eye in the viewer: things roofs.py carried up that
should not have moved, and things it left behind that should have.

Each entry records the height the box is expected to be at BEFORE the fix.
A box that is not at that height is skipped, not moved, so a rerun is a
no-op and an upstream change is reported rather than silently compounded.

GROW changes a box's extent as well as its origin, for cases where a lift
is not enough on its own. It defaults to the z axis; pass a fifth element
of 0 or 1 to grow along x or y instead.

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

    # Arch, 2026-08-16. The arch pierces axis_22, which roofs.py doubled
    # from 320.1 to 640.2. The arch itself was left at its original height,
    # so the opening was half the wall.
    #
    # The voussoirs are rotated boxes and a rotated box cannot be stretched
    # in z within an origin/extents/angles representation, so the arch is
    # not scaled. Instead the two piers are lengthened by 320.1 in GROW
    # below and the whole curve, crown and lintel are lifted by the same
    # amount, intact. The opening doubles, the arch keeps its radius, and
    # the springing line moves up. New crown top is 640.2, flush with the
    # top of axis_22.
    #
    # Note: axis_23, the platform above, has its underside at 666.9, so 26.7
    # remains between the crown and the platform. If flush to the platform
    # is wanted instead of flush to the wall, the delta is 346.8 throughout,
    # here and in GROW.
    'ramp-slab_1070': (188.2, 508.3),
    'ramp-slab_1071': (217.0, 537.1),
    'ramp-slab_1072': (243.9, 564.0),
    'ramp-slab_1073': (291.2, 611.3),
    'ramp-slab_1074': (284.6, 604.7),
    'ramp-slab_1075': (292.6, 612.7),
    'shallow_1076': (282.7, 602.8),
    'shallow_1077': (285.4, 605.5),
    'shallow_1078': (285.4, 605.5),
    'shallow_1079': (282.7, 602.8),
    'ramp-slab_1080': (292.6, 612.7),
    'ramp-slab_1081': (284.6, 604.7),
    'ramp_1082': (275.1, 595.2),
    'ramp-slab_1083': (263.2, 583.3),
    'ramp-slab_1084': (253.1, 573.2),
    'ramp-slab_1085': (225.5, 545.6),
    'ramp-slab_1086': (218.7, 538.8),
    'ramp-slab_1087': (201.5, 521.6),
    'ramp-slab_1088': (188.9, 509.0),
    'axis_20': (306.7, 626.8),

    # Arch B, 2026-08-16. Identical in construction to the arch above:
    # piers axis_4 and axis_5 at 186.7 tall, crown at 320.1, and the walls
    # beside it (axis_7, axis_16) already doubled to 640.2. Same delta of
    # 320.1, same treatment: piers lengthened in GROW, curve and lintel
    # lifted intact.
    'ramp-slab_801': (192.7, 512.8),
    'ramp-slab_802': (219.2, 539.3),
    'ramp-slab_803': (244.2, 564.3),
    'ramp-slab_804': (288.4, 608.5),
    'ramp-slab_805': (282.1, 602.2),
    'ramp-slab_806': (289.6, 609.7),
    'ramp-slab_811': (289.6, 609.7),
    'ramp-slab_812': (282.1, 602.2),
    'ramp-slab_813': (288.4, 608.5),
    'ramp-slab_814': (244.2, 564.3),
    'ramp-slab_815': (219.2, 539.3),
    'ramp-slab_816': (192.7, 512.8),
    'shallow_807': (283.4, 603.5),
    'shallow_810': (283.4, 603.5),
    'merged_808': (285.9, 606.0),
    'axis_19': (306.7, 626.8),

    # Arch A, 2026-08-16, corrected. axis_483 was NOT a safe reference: it
    # is itself 213.0 too high. axis_468, the long wall running along the
    # map edge, is the datum, at 213.4 to 1067.0, and axis_483 shares its
    # 853.6 height but starts at 426.4. Lowered onto it here.
    #
    # The arch went up with it, so the whole assembly comes down the same
    # 213.0. Net against the original plan the curve moves +213.8: up 426.8
    # for the doubling it missed, down 213.0 for the base that was wrong.
    # Piers are rebased to 213.4 in GROW. New crown top is 1067.1 against
    # axis_468's 1067.0.
    'axis_483': (853.2, 640.2),

    # Batch, 2026-08-16.
    # axis_378 raised 133.5 so its top meets axis_376's at 893.6. Height
    # unchanged at 400.0.
    'axis_378': (560.1, 693.6),
    # Doorway arch at y 3600, 2026-08-16. Levelled with axis_762, the roof
    # panel of the building it sits in, which tops out at 680.2. Delta 200.1
    # from the original head top of 480.1. NOT the wall top: the wall
    # axis_735 reaches 1067.0 and is not the reference here.
    #
    # shallow_916 and shallow_917 are its two crown plates. shallow_916 was
    # briefly raised to meet the roof panel axis_762; it is retargeted here
    # to travel with the rest of the head.
    'shallow_916': (472.6, 672.7),

    # Doorway arch at x 200, 2026-08-16. Same construction as the other two,
    # rotated: yaw plus and minus 90 instead of 0 and 180. Doubled from the
    # floor: head top 293.4 to 586.8, so the delta is 293.4.
    #
    # Two independent confirmations of that number. axis_130, the panel
    # above the head, lands at exactly 1280.3, the top of axis_128, keeping
    # its own height. And axis_711's underside, the interior ceiling,
    # doubles from 320.1 to 640.2, putting its top at 1280.4, the same wall
    # top.
    'ramp-slab_820': (198.2, 491.6),
    'ramp-slab_821': (227.9, 521.3),
    'ramp-slab_822': (253.7, 547.1),
    'ramp-slab_833': (253.7, 547.1),
    'ramp-slab_834': (227.9, 521.3),
    'ramp-slab_835': (198.2, 491.6),
    'ramp_823': (267.6, 561.0),
    'ramp_824': (274.2, 567.6),
    'ramp_825': (279.2, 572.6),
    'ramp_826': (283.4, 576.8),
    'ramp_829': (283.4, 576.8),
    'ramp_830': (279.2, 572.6),
    'ramp_831': (274.2, 567.6),
    'ramp_832': (267.6, 561.0),
    'shallow_827': (285.9, 579.3),
    'shallow_828': (285.9, 579.3),
    # axis_130, the panel above the head, takes the same 293.4 and lands at
    # 1280.3, the top of axis_128. It keeps its 693.4 height.
    'axis_130': (640.2, 933.6),
    # axis_711 is the interior ceiling: a 640.2 thick slab whose UNDERSIDE
    # at 320.1 is what reads as the ceiling. Doubling that from the floor
    # puts the underside at 640.2 and its top at 1280.4, the wall top again.
    'axis_711': (640.2, 960.3),
    # axis_763 and axis_768 tile the interior ceiling west of the door,
    # axis_768 over y 3174 to 3307 and axis_763 over y 3307 to 3520. They
    # ran 466.8 to 506.8, leaving the crown standing 80 proud of the
    # ceiling. Raised 80.0 so their tops meet the crown at 586.8, which is
    # how the other two doors already sit against axis_762 and axis_766.
    'axis_763': (486.8, 566.8),
    'axis_768': (486.8, 566.8),

    # Interior doorframe arch at y 3161, 2026-08-16. Head raised 266.7 so
    # its crown tops out at 586.8, level with axis_768's ceiling. Springing
    # goes to 462.2, above the jamb tops of 426.8, so axis_717 and axis_718
    # are extended in GROW.
    'ramp-slab_893': (222.2, 488.9),
    'ramp-slab_895': (276.9, 543.6),
    'ramp-slab_906': (276.9, 543.6),
    'ramp-slab_908': (222.2, 488.9),
    'ramp_896': (294.2, 560.9),
    'ramp_897': (300.9, 567.6),
    'ramp_898': (305.9, 572.6),
    'ramp_899': (310.1, 576.8),
    'ramp_902': (310.1, 576.8),
    'ramp_903': (305.9, 572.6),
    'ramp_904': (300.9, 567.6),
    'ramp_905': (294.2, 560.9),
    'merged_900': (312.6, 579.3),
    'ramp-slab_909': (384.6, 584.7),
    'ramp-slab_910': (414.2, 614.3),
    'ramp-slab_911': (440.1, 640.2),
    'ramp-slab_922': (440.1, 640.2),
    'ramp-slab_923': (414.2, 614.3),
    'ramp-slab_924': (384.6, 584.7),
    'ramp_912': (454.3, 654.4),
    'ramp_913': (460.9, 661.0),
    'ramp_914': (465.9, 666.0),
    'ramp_915': (470.1, 670.2),
    'ramp_918': (470.1, 670.2),
    'ramp_919': (465.9, 666.0),
    'ramp_920': (460.9, 661.0),
    'ramp_921': (454.3, 654.4),
    'shallow_917': (472.6, 672.7),
    'axis_734': (560.1, 760.2),

    # Doorway arch at y 2227, 2026-08-16. Levelled with axis_766, the roof
    # panel of the same building, which tops out at 720.2. Delta 240.1 from
    # the original head top of 480.1. There are no jambs: nothing exists
    # between the floor at 253.4 and the springing at 358.0, so the head
    # rises and the opening below it gets taller.
    #
    # shallow_884 and shallow_885 are the two central crown plates, touching
    # at x -1333.6, both 23.2 x 26.7 x 15.0 and both originally at 465.1 to
    # 480.1. shallow_885 was briefly raised to meet the roof panel axis_766,
    # which pulled a keystone out of this arch; it is retargeted here to
    # travel with the rest of the head.
    'shallow_885': (472.6, 712.7),
    'ramp-slab_877': (384.6, 624.7),
    'ramp-slab_878': (414.2, 654.3),
    'ramp-slab_879': (440.1, 680.2),
    'ramp-slab_890': (440.1, 680.2),
    'ramp-slab_891': (414.2, 654.3),
    'ramp-slab_892': (384.6, 624.7),
    'ramp_880': (454.3, 694.4),
    'ramp_881': (460.9, 701.0),
    'ramp_882': (465.9, 706.0),
    'ramp_883': (470.1, 710.2),
    'ramp_886': (470.1, 710.2),
    'ramp_887': (465.9, 706.0),
    'ramp_888': (460.9, 701.0),
    'ramp_889': (454.3, 694.4),
    'shallow_884': (472.6, 712.7),
    'axis_583': (560.1, 800.2),
    # Two 160 crates that sat at 720.2 to 880.2 with nothing under them,
    # dropped onto axis_62's floor at 346.8.
    'axis_67': (800.2, 426.8),
    'axis_65': (800.2, 426.8),
    'ramp-slab_861': (693.2, 907.0),
    'ramp-slab_862': (733.2, 947.0),
    'ramp-slab_863': (770.2, 984.0),
    'ramp-slab_864': (837.0, 1050.8),
    'ramp-slab_865': (828.0, 1041.8),
    'ramp-slab_866': (839.2, 1053.0),
    'ramp-slab_871': (839.2, 1053.0),
    'ramp-slab_872': (828.0, 1041.8),
    'ramp-slab_873': (837.0, 1050.8),
    'ramp-slab_874': (770.2, 984.0),
    'ramp-slab_875': (733.2, 947.0),
    'ramp-slab_876': (693.2, 907.0),
    'shallow_867': (838.8, 1052.6),
    'shallow_868': (842.4, 1056.2),
    'shallow_869': (842.4, 1056.2),
    'shallow_870': (838.8, 1052.6),

    # Arch C, 2026-08-16. Not several arches: one barrel vault extruded 800
    # units along y, which is why it reads as a tunnel. Every element shares
    # y 506.8 and an 800 y-extent.
    #
    # No pier work here. It springs off axis_454 and axis_457, which are
    # already doubled to 213.4 through 1067.0, so this is a pure lift of
    # 426.8. axis_456, the deck resting on the vault, is included: it tops
    # out at 640.1, the walls' pre-doubling height, and lands at 1066.9,
    # the doubled wall top. Leaving it behind would strand it.
    'ramp-slab_845': (491.3, 918.1),
    'ramp-slab_846': (520.9, 947.7),
    'ramp-slab_847': (546.8, 973.6),
    'ramp-slab_858': (546.8, 973.6),
    'ramp-slab_859': (520.9, 947.7),
    'ramp-slab_860': (491.3, 918.1),
    'ramp_848': (560.9, 987.7),
    'ramp_849': (567.6, 994.4),
    'ramp_850': (572.6, 999.4),
    'ramp_851': (576.8, 1003.6),
    'ramp_854': (576.8, 1003.6),
    'ramp_855': (572.6, 999.4),
    'ramp_856': (567.6, 994.4),
    'ramp_857': (560.9, 987.7),
    'shallow_852': (579.3, 1006.1),
    'shallow_853': (579.3, 1006.1),
    'axis_456': (613.5, 1040.3),
}


# name: (was_origin, now_origin, was_extent, now_extent[, axis=2])
GROW = {
    # Arch piers, 2026-08-16. See the arch note in FIXES. Both run from 0.1
    # and are lengthened by 320.1 so the arch curve lands on top of them at
    # its new height, rather than the arch floating clear of its legs.
    'axis_18': (93.4, 253.5, 186.7, 506.8),
    'axis_2': (93.4, 253.5, 186.7, 506.8),

    # Wall trim, 2026-08-16. axis_68 ran 346.7 to 933.5 through a space it
    # should not close off, but it serves a function above, so it is
    # shortened from below rather than moved or removed. New base is 640.1,
    # the underside of merged_84. The top stays at 933.5 and axis_355, which
    # crosses this footprint at 826.9 to 853.6, is well inside the surviving
    # span. Height 586.8 to 293.4.
    'axis_68': (640.1, 786.8, 586.8, 293.4),

    # Arch B piers, 2026-08-16. Same dimensions as the first arch's piers.
    'axis_4': (93.4, 253.5, 186.7, 506.8),
    'axis_5': (93.4, 253.5, 186.7, 506.8),

    # Arch A piers, 2026-08-16. Rebased from 426.4 to 213.4, the foot of
    # axis_468, and lengthened so they top out at 911.8 with the lifted
    # curve landing on them rather than floating clear.
    'axis_480': (562.2, 562.6, 271.6, 698.4),
    'axis_481': (562.2, 562.6, 271.6, 698.4),

    # axis_1 extended along Y, 2026-08-16. It ended at y 4960.9 and axis_61
    # begins at y 5067.6, leaving a 106.7 opening. Lengthened to close it:
    # y extent 480.1 to 586.8. Height and thickness untouched.
    'axis_1': (4720.9, 4774.2, 480.1, 586.8, 1),

    # Doorframe jambs at y 3161, 2026-08-16. Taken from 426.8 up to 586.8,
    # level with the crown and the ceiling. NOT grown by the arch's own
    # 266.7, which would top them at 693.5 and punch through the ceiling
    # they stand under.
    'axis_717': (213.4, 293.4, 426.8, 586.8),
    'axis_718': (213.4, 293.4, 426.8, 586.8),

    # axis_719 grown 120.0, 2026-08-16, from 560.2 up to axis_766's
    # underside at 680.2. The two overlap in only a 26.8 wide strip in x,
    # so this is a narrow join rather than a full bearing.
    'axis_719': (280.1, 340.1, 560.2, 680.2),

    # axis_81 halved above axis_122, 2026-08-16. It stood 320.2 proud of
    # axis_122's top at 213.3; that is halved to 160.1, so the wall tops out
    # at 373.4. Base unchanged at 0.1, height 533.4 to 373.3.
    'axis_81': (266.8, 186.8, 533.4, 373.3),

    # Arcade infill panels, 2026-08-16. merged_97 and merged_98 ran 346.7 to
    # 933.5 and hung below the arch head into the opening. Rebased to 666.9,
    # the top of the string course axis_83, which runs the whole length
    # under them and itself sits on the lintel axis_19 at 613.4 to 640.1.
    # Top unchanged at 933.5, height 586.8 to 266.6.
    #
    # merged_99 is deliberately NOT here. It sits past the pier axis_4 at
    # y 4507.6 to 4747.6, over the solid wall axis_3, so its low edge is
    # buried rather than hanging.
    'merged_97': (640.1, 800.2, 586.8, 266.6),
    'merged_98': (640.1, 800.2, 586.8, 266.6),
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

for name, spec in GROW.items():
    was_o, now_o, was_e, now_e = spec[:4]
    ax = spec[4] if len(spec) > 4 else 2
    box = by_name.get(name)
    if box is None:
        missing.append(name)
        continue
    o, e = box['origin'][ax], box['extents'][ax]
    if abs(o - was_o) > TOL or abs(e - was_e) > TOL:
        skipped.append((name, o, was_o))
        continue
    box['origin'][ax] = now_o
    box['extents'][ax] = now_e
    moved.append(name)

json.dump(p, open('dust2_half.json', 'w'), indent=1)

print(f'moved {len(moved)} of {len(FIXES) + len(GROW)} listed')
for name, z, was in skipped:
    print(f'  skipped {name}: z={z}, expected {was}')
for name in missing:
    print(f'  NOT FOUND (already gone or renamed): {name}')
