"""Manual additions, batched.

Boxes defined here are appended to the plan. This is the list for geometry
that had to be rebuilt by hand because an automated rule produced the wrong
shape and deleting the result is not enough on its own.

Run after remove.py, before treefix.py.
"""
import json

ADD = [
    # Replaces shallow_52 and gapfill_38_45, 2026-08-16.
    #
    # shallow_52 was a ramp that simplify.py flattened to a level plate with
    # its top at 133.3. ramp-slab_53 is the same physical slope and survived
    # at pitch 10.62, so one ramp was split either side of the 10 degree
    # cutoff and half of it became terrain. gapfill.py then filled the void
    # above the flat plate to 213.4, which is the platform you could stand
    # on. Both are removed in remove.py.
    #
    # This slab runs west to east from z 0 at x 1920 up to z 132.9 at
    # x 2772, which is the west edge of ramp-slab_53's top face once its
    # 10.62 pitch is applied. Grade is 8.87 degrees against ramp-slab_53's
    # 10.62. Not a constant grade across the pair, but continuous at the
    # join, which is what the two ends actually are.
    #
    # Thickness is 160, matching the plate it replaces. That is enough that
    # the underside stays below ground level along the whole run (-161.9 at
    # the west end, -29.0 at the east), so the space under the ramp is
    # sealed without re-running gapfill.
    # Seven more arched doors, 2026-08-16, same arch and method as the
    # axis_450 one. Each is centred on its crosshair along the wall's run
    # and offset in z so it stands on that wall's own floor.
    #
    # For the four walls running in x (axis_479, axis_191, axis_124 and the
    # rotated pair) the arch is turned 90 degrees. Extents are stored in the
    # LOCAL frame and the angles do the mapping, so that is yaw plus 90 with
    # the origins rotated about the arch centre, NOT an extent swap.
    #
    # axis_57 was crosshaired but is a 26.7 plate at the far side of the
    # map; the box actually under that crosshair is axis_574, so the door
    # went there.
    {
        'name': 'ramp-slab_820_d462',
        'origin': [-13.3, 1390.1, 491.7],
        'extents': [44.5, 26.7, 53.3],
        'angles': [40.71, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_821_d462',
        'origin': [-13.3, 1392.2, 521.4],
        'extents': [55.3, 26.7, 53.3],
        'angles': [54.61, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_822_d462',
        'origin': [-13.3, 1389.6, 547.2],
        'extents': [73.7, 26.7, 53.3],
        'angles': [58.86, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_833_d462',
        'origin': [-13.3, 1168.5, 547.2],
        'extents': [73.7, 26.7, 53.3],
        'angles': [58.86, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_834_d462',
        'origin': [-13.3, 1165.8, 521.4],
        'extents': [55.3, 26.7, 53.3],
        'angles': [54.61, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_835_d462',
        'origin': [-13.3, 1168.0, 491.7],
        'extents': [44.5, 26.7, 53.3],
        'angles': [40.69, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_823_d462',
        'origin': [-13.3, 1361.4, 561.1],
        'extents': [26.7, 42.0, 51.7],
        'angles': [50.90, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_824_d462',
        'origin': [-13.3, 1340.9, 567.7],
        'extents': [26.7, 29.0, 38.3],
        'angles': [52.88, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_825_d462',
        'origin': [-13.3, 1324.9, 572.7],
        'extents': [26.7, 25.0, 28.3],
        'angles': [48.54, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_826_d462',
        'origin': [-13.3, 1307.9, 576.9],
        'extents': [26.7, 23.2, 20.0],
        'angles': [40.74, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_829_d462',
        'origin': [-13.3, 1250.2, 576.9],
        'extents': [26.7, 23.2, 20.0],
        'angles': [40.74, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_830_d462',
        'origin': [-13.3, 1233.1, 572.7],
        'extents': [26.7, 25.0, 28.3],
        'angles': [48.54, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_831_d462',
        'origin': [-13.3, 1217.1, 567.7],
        'extents': [26.7, 29.0, 38.3],
        'angles': [52.88, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_832_d462',
        'origin': [-13.3, 1196.7, 561.1],
        'extents': [26.7, 42.0, 51.7],
        'angles': [50.90, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'shallow_827_d462',
        'origin': [-13.3, 1290.3, 579.4],
        'extents': [26.7, 22.5, 15.0],
        'angles': [0.00, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'shallow_828_d462',
        'origin': [-13.3, 1267.8, 579.4],
        'extents': [26.7, 22.5, 15.0],
        'angles': [0.00, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_462_hdr',
        'origin': [-13.3, 1279.0, 933.6],
        'extents': [26.7, 253.0, 693.3],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_462_far',
        'origin': [-13.3, 1462.9, 640.2],
        'extents': [26.7, 114.8, 1280.2],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_820_d479',
        'origin': [-108.1, -226.7, 705.0],
        'extents': [44.5, 26.7, 53.3],
        'angles': [40.71, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_821_d479',
        'origin': [-110.2, -226.7, 734.7],
        'extents': [55.3, 26.7, 53.3],
        'angles': [54.61, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_822_d479',
        'origin': [-107.6, -226.7, 760.5],
        'extents': [73.7, 26.7, 53.3],
        'angles': [58.86, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_833_d479',
        'origin': [113.5, -226.7, 760.5],
        'extents': [73.7, 26.7, 53.3],
        'angles': [58.86, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_834_d479',
        'origin': [116.2, -226.7, 734.7],
        'extents': [55.3, 26.7, 53.3],
        'angles': [54.61, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_835_d479',
        'origin': [114.0, -226.7, 705.0],
        'extents': [44.5, 26.7, 53.3],
        'angles': [40.69, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_823_d479',
        'origin': [-79.4, -226.7, 774.4],
        'extents': [26.7, 42.0, 51.7],
        'angles': [50.90, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_824_d479',
        'origin': [-58.9, -226.7, 781.0],
        'extents': [26.7, 29.0, 38.3],
        'angles': [52.88, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_825_d479',
        'origin': [-42.9, -226.7, 786.0],
        'extents': [26.7, 25.0, 28.3],
        'angles': [48.54, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_826_d479',
        'origin': [-25.9, -226.7, 790.2],
        'extents': [26.7, 23.2, 20.0],
        'angles': [40.74, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_829_d479',
        'origin': [31.8, -226.7, 790.2],
        'extents': [26.7, 23.2, 20.0],
        'angles': [40.74, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_830_d479',
        'origin': [48.9, -226.7, 786.0],
        'extents': [26.7, 25.0, 28.3],
        'angles': [48.54, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_831_d479',
        'origin': [64.9, -226.7, 781.0],
        'extents': [26.7, 29.0, 38.3],
        'angles': [52.88, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_832_d479',
        'origin': [85.3, -226.7, 774.4],
        'extents': [26.7, 42.0, 51.7],
        'angles': [50.90, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'shallow_827_d479',
        'origin': [-8.3, -226.7, 792.7],
        'extents': [26.7, 22.5, 15.0],
        'angles': [0.00, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'shallow_828_d479',
        'origin': [14.2, -226.7, 792.7],
        'extents': [26.7, 22.5, 15.0],
        'angles': [0.00, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_479_hdr',
        'origin': [3.0, -226.7, 933.6],
        'extents': [253.0, 26.7, 266.8],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_479_far',
        'origin': [158.1, -226.7, 640.2],
        'extents': [57.2, 26.7, 853.6],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_820_d195',
        'origin': [2280.5, 950.1, 491.7],
        'extents': [44.5, 26.7, 53.3],
        'angles': [40.71, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_821_d195',
        'origin': [2280.5, 952.2, 521.4],
        'extents': [55.3, 26.7, 53.3],
        'angles': [54.61, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_822_d195',
        'origin': [2280.5, 949.6, 547.2],
        'extents': [73.7, 26.7, 53.3],
        'angles': [58.86, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_833_d195',
        'origin': [2280.5, 728.5, 547.2],
        'extents': [73.7, 26.7, 53.3],
        'angles': [58.86, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_834_d195',
        'origin': [2280.5, 725.8, 521.4],
        'extents': [55.3, 26.7, 53.3],
        'angles': [54.61, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_835_d195',
        'origin': [2280.5, 728.0, 491.7],
        'extents': [44.5, 26.7, 53.3],
        'angles': [40.69, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_823_d195',
        'origin': [2280.5, 921.4, 561.1],
        'extents': [26.7, 42.0, 51.7],
        'angles': [50.90, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_824_d195',
        'origin': [2280.5, 900.9, 567.7],
        'extents': [26.7, 29.0, 38.3],
        'angles': [52.88, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_825_d195',
        'origin': [2280.5, 884.9, 572.7],
        'extents': [26.7, 25.0, 28.3],
        'angles': [48.54, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_826_d195',
        'origin': [2280.5, 867.9, 576.9],
        'extents': [26.7, 23.2, 20.0],
        'angles': [40.74, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_829_d195',
        'origin': [2280.5, 810.2, 576.9],
        'extents': [26.7, 23.2, 20.0],
        'angles': [40.74, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_830_d195',
        'origin': [2280.5, 793.1, 572.7],
        'extents': [26.7, 25.0, 28.3],
        'angles': [48.54, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_831_d195',
        'origin': [2280.5, 777.1, 567.7],
        'extents': [26.7, 29.0, 38.3],
        'angles': [52.88, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_832_d195',
        'origin': [2280.5, 756.7, 561.1],
        'extents': [26.7, 42.0, 51.7],
        'angles': [50.90, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'shallow_827_d195',
        'origin': [2280.5, 850.3, 579.4],
        'extents': [26.7, 22.5, 15.0],
        'angles': [0.00, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'shallow_828_d195',
        'origin': [2280.5, 827.8, 579.4],
        'extents': [26.7, 22.5, 15.0],
        'angles': [0.00, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_195_hdr',
        'origin': [2280.5, 839.0, 933.6],
        'extents': [26.7, 253.0, 693.3],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_195_far',
        'origin': [2280.5, 1516.3, 640.2],
        'extents': [26.7, 1101.6, 1280.2],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_820_d191',
        'origin': [2775.9, 2760.6, 491.7],
        'extents': [44.5, 26.7, 53.3],
        'angles': [40.71, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_821_d191',
        'origin': [2773.8, 2760.6, 521.4],
        'extents': [55.3, 26.7, 53.3],
        'angles': [54.61, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_822_d191',
        'origin': [2776.4, 2760.6, 547.2],
        'extents': [73.7, 26.7, 53.3],
        'angles': [58.86, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_833_d191',
        'origin': [2997.5, 2760.6, 547.2],
        'extents': [73.7, 26.7, 53.3],
        'angles': [58.86, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_834_d191',
        'origin': [3000.2, 2760.6, 521.4],
        'extents': [55.3, 26.7, 53.3],
        'angles': [54.61, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_835_d191',
        'origin': [2998.0, 2760.6, 491.7],
        'extents': [44.5, 26.7, 53.3],
        'angles': [40.69, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_823_d191',
        'origin': [2804.6, 2760.6, 561.1],
        'extents': [26.7, 42.0, 51.7],
        'angles': [50.90, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_824_d191',
        'origin': [2825.1, 2760.6, 567.7],
        'extents': [26.7, 29.0, 38.3],
        'angles': [52.88, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_825_d191',
        'origin': [2841.1, 2760.6, 572.7],
        'extents': [26.7, 25.0, 28.3],
        'angles': [48.54, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_826_d191',
        'origin': [2858.1, 2760.6, 576.9],
        'extents': [26.7, 23.2, 20.0],
        'angles': [40.74, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_829_d191',
        'origin': [2915.8, 2760.6, 576.9],
        'extents': [26.7, 23.2, 20.0],
        'angles': [40.74, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_830_d191',
        'origin': [2932.9, 2760.6, 572.7],
        'extents': [26.7, 25.0, 28.3],
        'angles': [48.54, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_831_d191',
        'origin': [2948.9, 2760.6, 567.7],
        'extents': [26.7, 29.0, 38.3],
        'angles': [52.88, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_832_d191',
        'origin': [2969.3, 2760.6, 561.1],
        'extents': [26.7, 42.0, 51.7],
        'angles': [50.90, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'shallow_827_d191',
        'origin': [2875.7, 2760.6, 579.4],
        'extents': [26.7, 22.5, 15.0],
        'angles': [0.00, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'shallow_828_d191',
        'origin': [2898.2, 2760.6, 579.4],
        'extents': [26.7, 22.5, 15.0],
        'angles': [0.00, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_191_hdr',
        'origin': [2887.0, 2760.6, 933.6],
        'extents': [253.2, 26.7, 693.3],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_191_far',
        'origin': [3107.1, 2760.6, 640.2],
        'extents': [187.0, 26.7, 1280.2],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_820_d124',
        'origin': [1115.9, 1453.6, 491.7],
        'extents': [44.5, 26.7, 53.3],
        'angles': [40.71, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_821_d124',
        'origin': [1113.8, 1453.6, 521.4],
        'extents': [55.3, 26.7, 53.3],
        'angles': [54.61, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_822_d124',
        'origin': [1116.4, 1453.6, 547.2],
        'extents': [73.7, 26.7, 53.3],
        'angles': [58.86, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_833_d124',
        'origin': [1337.5, 1453.6, 547.2],
        'extents': [73.7, 26.7, 53.3],
        'angles': [58.86, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_834_d124',
        'origin': [1340.2, 1453.6, 521.4],
        'extents': [55.3, 26.7, 53.3],
        'angles': [54.61, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_835_d124',
        'origin': [1338.0, 1453.6, 491.7],
        'extents': [44.5, 26.7, 53.3],
        'angles': [40.69, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_823_d124',
        'origin': [1144.6, 1453.6, 561.1],
        'extents': [26.7, 42.0, 51.7],
        'angles': [50.90, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_824_d124',
        'origin': [1165.1, 1453.6, 567.7],
        'extents': [26.7, 29.0, 38.3],
        'angles': [52.88, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_825_d124',
        'origin': [1181.1, 1453.6, 572.7],
        'extents': [26.7, 25.0, 28.3],
        'angles': [48.54, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_826_d124',
        'origin': [1198.1, 1453.6, 576.9],
        'extents': [26.7, 23.2, 20.0],
        'angles': [40.74, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_829_d124',
        'origin': [1255.8, 1453.6, 576.9],
        'extents': [26.7, 23.2, 20.0],
        'angles': [40.74, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_830_d124',
        'origin': [1272.9, 1453.6, 572.7],
        'extents': [26.7, 25.0, 28.3],
        'angles': [48.54, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_831_d124',
        'origin': [1288.9, 1453.6, 567.7],
        'extents': [26.7, 29.0, 38.3],
        'angles': [52.88, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_832_d124',
        'origin': [1309.3, 1453.6, 561.1],
        'extents': [26.7, 42.0, 51.7],
        'angles': [50.90, 180.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'shallow_827_d124',
        'origin': [1215.7, 1453.6, 579.4],
        'extents': [26.7, 22.5, 15.0],
        'angles': [0.00, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'shallow_828_d124',
        'origin': [1238.2, 1453.6, 579.4],
        'extents': [26.7, 22.5, 15.0],
        'angles': [0.00, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_124_hdr',
        'origin': [1227.0, 1453.6, 933.6],
        'extents': [253.0, 26.7, 693.3],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_124_far',
        'origin': [1637.0, 1453.6, 640.2],
        'extents': [567.0, 26.7, 1280.2],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Door 7 rebuilt on the second floor, 2026-08-16. Its first placement
    # was at y 1120 on the ground, where axis_769 does not reach. That floor
    # tops out at 653.5 and overlaps axis_574 only between y 2240.4 and
    # 2667.2, so the door is centred at y 2454 in that stretch. axis_769
    # runs x -853.5 to 186.7, straight through the wall, so the door
    # connects two parts of the same floor.
    # Door 7 rebuilt as a SECOND-FLOOR door in axis_733, 2026-08-16. It was
    # first placed on axis_574, which has no upper floor anywhere along it.
    # This sits directly above the ground-floor door already in axis_733,
    # sharing its opening at y 2893.4 to 3146.6, and stands on axis_769 at
    # 653.5. axis_574 is left whole.
    #
    # axis_733's old header, which ran 587.0 to 1280.2 across the opening,
    # is replaced by a sill under the new floor and a cap above the crown.
    # Door 7 on the axis_574 second floor, 2026-08-16. Stands on axis_769,
    # which tops out at 653.5 and overlaps axis_574 only between y 2240.4
    # and 2667.2; the door is centred at y 2454 in that stretch. axis_769
    # runs x -853.5 to 186.7, straight through the wall, so it connects two
    # parts of the same floor.
    # axis_733's door, 2026-08-16: SECOND FLOOR ONLY. The ground-floor
    # opening from the seven-door batch is gone and that stretch is solid
    # wall again up to 653.5, the top of axis_769. axis_574 keeps no door.
    #
    # Opening y 2893.5 to 3146.5, springing 1118.4, crown 1240.3, with a cap
    # to the wall top at 1280.3. The far strip beyond the opening is 0.8
    # wide so there is no panel there; the door runs to the wall's end.
    {
        'name': 'ramp-slab_820_d733',
        'origin': [-520.1, 3131.1, 1145.0],
        'extents': [44.5, 26.7, 53.3],
        'angles': [40.71, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_821_d733',
        'origin': [-520.1, 3133.2, 1174.7],
        'extents': [55.3, 26.7, 53.3],
        'angles': [54.61, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_822_d733',
        'origin': [-520.1, 3130.6, 1200.5],
        'extents': [73.7, 26.7, 53.3],
        'angles': [58.86, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_833_d733',
        'origin': [-520.1, 2909.5, 1200.5],
        'extents': [73.7, 26.7, 53.3],
        'angles': [58.86, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_834_d733',
        'origin': [-520.1, 2906.8, 1174.7],
        'extents': [55.3, 26.7, 53.3],
        'angles': [54.61, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_835_d733',
        'origin': [-520.1, 2909.0, 1145.0],
        'extents': [44.5, 26.7, 53.3],
        'angles': [40.69, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_823_d733',
        'origin': [-520.1, 3102.4, 1214.4],
        'extents': [26.7, 42.0, 51.7],
        'angles': [50.90, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_824_d733',
        'origin': [-520.1, 3081.9, 1221.0],
        'extents': [26.7, 29.0, 38.3],
        'angles': [52.88, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_825_d733',
        'origin': [-520.1, 3065.9, 1226.0],
        'extents': [26.7, 25.0, 28.3],
        'angles': [48.54, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_826_d733',
        'origin': [-520.1, 3048.9, 1230.2],
        'extents': [26.7, 23.2, 20.0],
        'angles': [40.74, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_829_d733',
        'origin': [-520.1, 2991.2, 1230.2],
        'extents': [26.7, 23.2, 20.0],
        'angles': [40.74, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_830_d733',
        'origin': [-520.1, 2974.1, 1226.0],
        'extents': [26.7, 25.0, 28.3],
        'angles': [48.54, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_831_d733',
        'origin': [-520.1, 2958.1, 1221.0],
        'extents': [26.7, 29.0, 38.3],
        'angles': [52.88, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_832_d733',
        'origin': [-520.1, 2937.7, 1214.4],
        'extents': [26.7, 42.0, 51.7],
        'angles': [50.90, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'shallow_827_d733',
        'origin': [-520.1, 3031.3, 1232.7],
        'extents': [26.7, 22.5, 15.0],
        'angles': [0.00, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'shallow_828_d733',
        'origin': [-520.1, 3008.8, 1232.7],
        'extents': [26.7, 22.5, 15.0],
        'angles': [0.00, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_733_low',
        'origin': [-520.1, 3020.0, 326.8],
        'extents': [26.7, 253.0, 653.4],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_733_hdr',
        'origin': [-520.1, 3020.0, 1260.2],
        'extents': [26.7, 253.0, 40.1],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # New arched door in axis_450, 2026-08-16. A copy of the x 200 doorway
    # arch. Both walls are 26.7 thick and run in y, so it is a pure
    # translation with no rotation: x +1280.3, y -2945.3 to centre it on
    # y 382, and z +213.4 to stand it on axis_450's floor rather than
    # sinking it below, since the original springs off z 0.
    #
    # The arch occupies y 255.4 to 508.5, so axis_450 is split: it becomes the
    # north panel in treefix.py, and the south panel and the header above
    # the crown are added here.
    {
        'name': 'ramp-slab_820_a450',
        'origin': [1480.3, 493.1, 705.0],
        'extents': [44.5, 26.7, 53.3],
        'angles': [40.71, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_821_a450',
        'origin': [1480.3, 495.2, 734.7],
        'extents': [55.3, 26.7, 53.3],
        'angles': [54.61, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_822_a450',
        'origin': [1480.3, 492.6, 760.5],
        'extents': [73.7, 26.7, 53.3],
        'angles': [58.86, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_833_a450',
        'origin': [1480.3, 271.5, 760.5],
        'extents': [73.7, 26.7, 53.3],
        'angles': [58.86, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_834_a450',
        'origin': [1480.3, 268.8, 734.7],
        'extents': [55.3, 26.7, 53.3],
        'angles': [54.61, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_835_a450',
        'origin': [1480.3, 271.0, 705.0],
        'extents': [44.5, 26.7, 53.3],
        'angles': [40.69, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_823_a450',
        'origin': [1480.3, 464.4, 774.4],
        'extents': [26.7, 42.0, 51.7],
        'angles': [50.90, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_824_a450',
        'origin': [1480.3, 443.9, 781.0],
        'extents': [26.7, 29.0, 38.3],
        'angles': [52.88, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_825_a450',
        'origin': [1480.3, 427.9, 786.0],
        'extents': [26.7, 25.0, 28.3],
        'angles': [48.54, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_826_a450',
        'origin': [1480.3, 410.9, 790.2],
        'extents': [26.7, 23.2, 20.0],
        'angles': [40.74, -90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_829_a450',
        'origin': [1480.3, 353.2, 790.2],
        'extents': [26.7, 23.2, 20.0],
        'angles': [40.74, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_830_a450',
        'origin': [1480.3, 336.1, 786.0],
        'extents': [26.7, 25.0, 28.3],
        'angles': [48.54, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_831_a450',
        'origin': [1480.3, 320.1, 781.0],
        'extents': [26.7, 29.0, 38.3],
        'angles': [52.88, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp_832_a450',
        'origin': [1480.3, 299.7, 774.4],
        'extents': [26.7, 42.0, 51.7],
        'angles': [50.90, 90.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'shallow_827_a450',
        'origin': [1480.3, 393.3, 792.7],
        'extents': [26.7, 22.5, 15.0],
        'angles': [0.00, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'shallow_828_a450',
        'origin': [1480.3, 370.8, 792.7],
        'extents': [26.7, 22.5, 15.0],
        'angles': [0.00, 0.00, 0.00],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_450_south',
        'origin': [1480.3, 221.1, 640.2],
        'extents': [26.7, 68.7, 853.6],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_450_header',
        'origin': [1480.3, 382.0, 933.6],
        'extents': [26.7, 253.1, 266.8],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Ceiling of the axis_192 / axis_195 bay, 2026-08-16. Sits inside all
    # four walls: x 1947.0 to 2267.2 and y 1153.6 to 2015.4, the latter
    # measured to the inner faces of the raised axis_202 and axis_198.
    # 26.7 thick, flush with their tops at 1280.3.
    {
        'name': 'ceiling_192_bay',
        'origin': [2107.1, 1584.5, 1267.0],
        'extents': [320.2, 861.8, 26.7],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Connector between axis_378 and axis_366, 2026-08-16. Spans ONLY the
    # portion axis_378 gained when it was raised: y 4054.2 to 4494.2 at
    # z 893.6 to 1280.3. The existing run below is deliberately untouched,
    # axis_376 topping out at 893.6 and ramp_843 at 853.5 to 873.5, both
    # clear of this box.
    {
        'name': 'gapfill_378_366',
        'origin': [-986.9, 4274.2, 1087.0],
        'extents': [53.3, 440.0, 386.7],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Fills between the axis_64/65/66/67 cubes, 2026-08-16. They form a 2x2
    # of 160 cubes with two gaps: 26.7 in x between the columns at 2133.7 to
    # 2160.4, and 53.4 in z between the levels at 506.8 to 560.2. These two
    # slots fill both, and their union with the four cubes is the complete
    # 2x2 volume. Done as two slots rather than one solid block so the cubes
    # stay distinct boxes instead of being buried inside it.
    {
        'name': 'gapfill_cubes_x',
        'origin': [2147.1, 5041.0, 533.5],
        'extents': [26.7, 160.0, 373.4],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'gapfill_cubes_z',
        'origin': [2147.1, 5041.0, 533.5],
        'extents': [346.7, 160.0, 53.4],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Box on the axis_82 step, 2026-08-16. Height is half of
    # gapfill_82_84's 293.3, so 146.7, sitting on the step's top at 346.8
    # and reaching 493.5. Footprint matches the step exactly, x 666.8 to
    # 1467.0 and y 3547.3 to 3734.0.
    #
    # Note this covers the WHOLE ledge, so the walkable step surface becomes
    # the top of this box instead. At 146.7 it is taller than the 120 hero,
    # so it reads as full cover rather than something to vault.
    {
        'name': 'cover_82',
        'origin': [1066.9, 3640.7, 420.2],
        'extents': [800.2, 186.7, 146.7],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Ceiling of the building, 2026-08-16. The sixteen walls raised in
    # treefix.py enclose x -2133.8 to -626.8 and y 2240.4 to 3587.3 measured
    # to their INNER faces, capped flush with the new wall tops at 1280.3.
    #
    # Extended east on 2026-08-16 to axis_733's inner face at -533.5. The
    # east boundary is not straight: axis_733 only runs y 2693.9 to 3147.3,
    # so south of that the ceiling projects 66.6 past axis_574's east face
    # at -600.1 over the strip y 2240.4 to 2667.2, and north of it the
    # corner is buried inside axis_711, which spans 640.2 to 1280.4 there.
    {
        'name': 'ceiling_553_block',
        'origin': [-1333.7, 2913.9, 1267.0],
        'extents': [1600.3, 1346.9, 26.7],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Connector between axis_377 and axis_378, 2026-08-16. Both are on the
    # same wall plane at x -1013.5 to -960.2, with a 133.6 void between
    # axis_377's top at 360.0 and axis_378's base at 493.6. This fills that
    # over the 253.4 of y they share.
    {
        'name': 'gapfill_377_378',
        'origin': [-986.9, 4620.9, 426.8],
        'extents': [53.3, 253.4, 133.6],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Floor of the alcove bounded by axis_265, axis_337, axis_557 and
    # axis_339, 2026-08-16. It had no floor at all: nothing between the
    # ground plane's top at -0.1 and 213.4, so it read as a hole you drop
    # into. Everything around it is floored, axis_193 to the south at 213.3
    # and gapfill_50_21 to the east at 213.4. Filled to 213.4 to match the
    # neighbouring gapfills; the 0.1 lip against axis_193 is far under the
    # 30 step height.
    {
        'name': 'gapfill_337_339',
        'origin': [2894.0, 1426.9, 106.7],
        'extents': [240.1, 133.4, 213.4],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Wall above the arcade, 2026-08-16, connecting axis_80 to axis_61.
    # axis_80 stops at y 3867.4 and axis_61 begins at 5067.6. Extending
    # axis_80 bodily in y would swallow the whole arcade, arch B included,
    # so this is the wall ABOVE the window band only: from the panel tops at
    # 933.5 up to 1280.3, axis_61's height. The heads axis_109, axis_111 and
    # axis_113 poke into its underside, which is harmless, and it overlaps
    # axis_371 over the last 160 of the run.
    {
        'name': 'gapfill_80_61',
        'origin': [653.5, 4467.5, 1106.9],
        'extents': [26.7, 1200.2, 346.8],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Wall above axis_68, 2026-08-16, bringing it to axis_61's height. Same
    # treatment: one box from the panel tops at 933.5 to 1280.3, running the
    # full length so the window bays are closed above their heads.
    {
        'name': 'axis_68_upper',
        'origin': [1480.3, 4254.3, 1106.9],
        'extents': [26.7, 1626.9, 346.8],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Windows in axis_68, 2026-08-16. Copies the pattern from the x 653.5
    # wall: solid panels separated by openings with a solid block below and
    # above. The three openings are lined up with the existing ones at
    # y 4187.6, 4454.2 and 4747.7, so the windows face their counterparts.
    #
    # The aperture is IDENTICAL to the source at 720.1 to 880.2, 160.1 tall.
    # Heads run 880.2 to 960.2 like axis_109, axis_111 and axis_113, so they
    # stand 26.7 proud of the panel tops exactly as those do.
    #
    # Below the aperture this uses a single block from 640.1 to 720.1 rather
    # than the source's two-part stack of axis_83's course at 640.1 to 666.9
    # plus a sill at 666.9 to 720.1, because axis_68 has no course under it
    # and the joint line would be invisible in a blockout.
    #
    # axis_68 itself is reshaped into the first panel in treefix.py; these
    # are the other three panels and the six blocks.
    {
        'name': 'axis_68_p2',
        'origin': [1480.3, 4347.5, 786.8],
        'extents': [26.7, 213.4, 293.4],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_68_p3',
        'origin': [1480.3, 4627.6, 786.8],
        'extents': [26.7, 240.2, 293.4],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_68_p4',
        'origin': [1480.3, 4934.3, 786.8],
        'extents': [26.7, 266.8, 293.4],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_68_sill1',
        'origin': [1480.3, 4214.2, 680.1],
        'extents': [26.7, 53.2, 80.0],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_68_head1',
        'origin': [1480.3, 4214.2, 920.2],
        'extents': [26.7, 53.2, 80.0],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_68_sill2',
        'origin': [1480.3, 4480.9, 680.1],
        'extents': [26.7, 53.3, 80.0],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_68_head2',
        'origin': [1480.3, 4480.9, 920.2],
        'extents': [26.7, 53.3, 80.0],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_68_sill3',
        'origin': [1480.3, 4774.3, 680.1],
        'extents': [26.7, 53.2, 80.0],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'axis_68_head3',
        'origin': [1480.3, 4774.3, 920.2],
        'extents': [26.7, 53.2, 80.0],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Connector between merged_119 and axis_68, 2026-08-16. Both are the
    # same 26.7 wall plane at x 1467.0, stacked with 266.7 of nothing
    # between 373.4 and 640.1. This fills that over the 293.4 of y they
    # share. The volume was completely empty.
    {
        'name': 'gapfill_119_68',
        'origin': [1480.3, 3587.4, 506.8],
        'extents': [26.7, 293.4, 266.7],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Fill between axis_69 and merged_84, 2026-08-16. Unlike the seam these
    # two overlap in plan: merged_84 starts at y 3734.1 and axis_69 runs to
    # 3867.5, a 133.4 band, and the gap is the full 426.8 between the low
    # deck's top and the high deck's underside. It subsumes part of
    # gapfill_82_84 below, which is redundant but harmless, and it buries
    # axis_121.
    {
        'name': 'gapfill_69_84',
        'origin': [1327.0, 3800.8, 426.7],
        'extents': [1133.6, 133.4, 426.8],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Fill under axis_82, 2026-08-16. axis_69's deck tops out at 213.3 and
    # axis_82 starts at 320.0 directly above it, leaving a 106.7 void.
    # Filled across axis_82's whole footprint. It engulfs the thin walls
    # axis_80 and merged_119 that pass through, and buries ramp-slab_90,
    # the leftover stair stringer.
    {
        'name': 'gapfill_69_82',
        'origin': [1066.9, 3640.7, 266.7],
        'extents': [800.2, 186.7, 106.7],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Riser at the merged_84 seam, 2026-08-16. axis_82 ends at y 3734.0 and
    # merged_84 begins at 3734.1, so the two decks meet edge to edge with an
    # open face between 346.8 and 640.1. This straddles the seam at 53.5
    # thick, and tops out flush with merged_84's underside. Extended west on
    # 2026-08-16 to meet axis_80's east face at 666.9.
    {
        'name': 'gapfill_82_84',
        'origin': [1067.0, 3734.1, 493.5],
        'extents': [800.1, 53.5, 293.3],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    {
        'name': 'ramp-slab_9052',
        'origin': [2346.0, 4280.9, -14.5],
        'extents': [862.3, 667.0, 160.0],
        'angles': [8.866, 180.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Floor east of axis_195, 2026-08-17. The arched door d195 in that wall,
    # opening y 712.5 to 965.5, led onto nothing: east of the wall's face at
    # 2293.8 there was no geometry at all between y 133.3 and axis_193's
    # south edge at 1493.6. The only floor over there was gapfill_39_8,
    # which reaches x 2400.5 because a solid fill overshot THROUGH the wall,
    # not because there is a route.
    #
    # This fills the bay from gapfill_39_8's south face at 26.6 north to
    # axis_193, and east to 2747.2, the west face of axis_265, so the space
    # is bounded rather than ending in air. Solid from z 0 like the
    # neighbouring gapfills rather than a 26.7 plate, so there is no void
    # underneath. Top at 213.4 against axis_193's 213.3, a 0.1 lip, far
    # under the 30 step height.
    #
    # Checked against the whole plan: the only box it intersects is
    # gapfill_39_8, which is intended. Nothing is buried by it. The d195
    # arch springs at 465.1 and clears it entirely.
    {
        'name': 'gapfill_195_193',
        'origin': [2520.5, 760.1, 106.7],
        'extents': [453.4, 1467.0, 213.4],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Diagonal wall closing the south-east corner of the axis_195 bay,
    # 2026-08-17. Runs at 45 degrees from the south end of axis_265 at
    # y 960.2 down to axis_195, meeting its centreline at y 480.2. Same
    # 26.7 thickness and same full height as both walls it joins, 0.1 to
    # 1280.3.
    #
    # The d195 arch, opening y 712.5 to 965.5, is NORTH of where this meets
    # axis_195, so the door is on the inside of the enclosure.
    #
    # Yaw only, no extent swap: extents are the local frame and the 45 in
    # angles does the mapping. Length is 705.6 against a centreline run of
    # 678.9, so it overlaps 13.35 into each wall and the corners close.
    {
        'name': 'axis_265_195_diag',
        'origin': [2520.5, 720.2, 640.2],
        'extents': [705.6, 26.7, 1280.2],
        'angles': [0.0, 45.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
    # Second level over the axis_195 bay, 2026-08-17. A 26.7 plate with its
    # underside at 586.95, which is 0.05 above the d195 arch crown at
    # 586.9, so the doorway below stays clear at full height. Same
    # footprint as gapfill_195_193 below it, x 2293.8 to 2747.2 and y 26.6
    # to 1493.6, so it ends south at the same y the ground floor starts.
    #
    # It has no access of its own yet and axis_265_195_diag passes through
    # it, since that wall runs the full 0.1 to 1280.3.
    {
        'name': 'floor2_195_bay',
        'origin': [2520.5, 760.1, 600.3],
        'extents': [453.4, 1467.0, 26.7],
        'angles': [0.0, 0.0, 0.0],
        'material': 'materials/dev/reflectivity_30.vmat',
    },
]

p = json.load(open('dust2_half.json'))
before = len(p['boxes'])
existing = {b['name'] for b in p['boxes']}

added, clash = [], []
for box in ADD:
    if box['name'] in existing:
        clash.append(box['name'])
        continue
    p['boxes'].append(box)
    added.append(box['name'])

json.dump(p, open('dust2_half.json', 'w'), indent=1)

print(f'added {len(added)} of {len(ADD)} listed: {added}')
if clash:
    print(f'ALREADY PRESENT (not added again): {clash}')
print(f'plan {before} -> {len(p["boxes"])} boxes')
