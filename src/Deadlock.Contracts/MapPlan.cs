using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Deadlock.Contracts;

/// <summary>
/// THE SOURCE OF TRUTH for a layout, until the map moves into Hammer.
///
/// Settled 2026-08-14: the .vmap is a regenerated build artifact, not an
/// editing surface. This file is what a human, an agent or the HTML viewer
/// reads and writes. On the day Hammer opens the exported map, Hammer becomes
/// the source and this file goes stale BY DESIGN — that is the plan, not a
/// problem to solve.
///
/// Deliberately small. Lighting, ziplines, bosses, groups, selection sets and
/// paths are all out of scope: every one of them introduces shared elements,
/// and the emitter's whole simplification is that nothing in its scope is
/// shared, so nothing needs a GUID.
/// </summary>
public sealed class MapPlan
{
    /// <summary>Schema version of this file. Bump on breaking changes.</summary>
    [JsonPropertyName("version")]
    public int Version { get; set; } = 1;

    /// <summary>Free-text name; becomes the addon/map name on export.</summary>
    [JsonPropertyName("name")]
    public string Name { get; set; } = "untitled";

    /// <summary>
    /// Grid spacing in Source units. Origins are expected to be multiples of
    /// this; extents are NOT constrained. 64 is the working assumption, taken
    /// from the floor height read off dl_example.vmap, and is marked [?] in
    /// FINDINGS rather than [V].
    /// </summary>
    [JsonPropertyName("cell")]
    public double Cell { get; set; } = 64;

    [JsonPropertyName("boxes")]
    public List<MapBox> Boxes { get; set; } = new();

    [JsonPropertyName("entities")]
    public List<MapEntity> Entities { get; set; } = new();

    /// <summary>
    /// Splines the game follows: lane_marker_path for trooper lanes,
    /// citadel_zipline_path for ziplines. Added 2026-08-22 after reading a
    /// real lane path out of dl_example.vmap — the route is not in the
    /// keyvalues, it is the ordered list of child nodes.
    /// </summary>
    [JsonPropertyName("paths")]
    public List<MapPath> Paths { get; set; } = new();
}

/// <summary>
/// An axis-aligned box. Geometry is authored in LOCAL space centred on the
/// origin and placed by Origin/Angles, because CMapMesh carries the transform
/// and CDmePolygonMesh does not. Grid-derived boxes therefore never need
/// world-space vertices.
/// </summary>
public sealed class MapBox
{
    [JsonPropertyName("name")]
    public string? Name { get; set; }

    /// <summary>Centre of the box, in Source units. Expected on the grid.</summary>
    [JsonPropertyName("origin")]
    public double[] Origin { get; set; } = { 0, 0, 0 };

    /// <summary>Full size along each axis. Free, not snapped.</summary>
    [JsonPropertyName("extents")]
    public double[] Extents { get; set; } = { 64, 64, 64 };

    /// <summary>Pitch, yaw, roll. Usually zero for a blockout.</summary>
    [JsonPropertyName("angles")]
    public double[] Angles { get; set; } = { 0, 0, 0 };

    [JsonPropertyName("material")]
    public string Material { get; set; } = "materials/dev/reflectivity_30.vmat";
}

/// <summary>
/// A point entity. Properties are a flat string-to-string bag because that is
/// exactly what EditGameClassProps is in the file: even numeric keys such as
/// lanenum and teamnumber are stored as strings.
/// </summary>
public sealed class MapEntity
{
    [JsonPropertyName("classname")]
    public string ClassName { get; set; } = "info_team_spawn";

    [JsonPropertyName("origin")]
    public double[] Origin { get; set; } = { 0, 0, 0 };

    [JsonPropertyName("angles")]
    public double[] Angles { get; set; } = { 0, 0, 0 };

    [JsonPropertyName("properties")]
    public Dictionary<string, string> Properties { get; set; } = new();

    /// <summary>
    /// Optional child geometry, for BRUSH entities. A trigger_item_shop or a
    /// func_nav_markup is a volume, not a point: in dl_example its CMapEntity
    /// holds a CMapMesh inline in `children`, exactly the way a CMapPath holds
    /// its nodes. Read verbatim 2026-08-22, not inferred.
    ///
    /// Extents and angles are LOCAL to the entity's own origin, matching how a
    /// box works everywhere else in this file. Leave null for a point entity —
    /// which is nearly all of them.
    ///
    /// NOT the same as the `model` keyvalue. A destroyable_building carries
    /// model = models/props_street/generator.vmdl and an EMPTY children array;
    /// a brush entity carries a child mesh and no model. Props and volumes are
    /// different things and this field is only for the second.
    /// </summary>
    [JsonPropertyName("mesh")]
    public MapBox? Mesh { get; set; }

    /// <summary>
    /// Entity IO. A shop is enabled and disabled by relays rather than
    /// directly, so most wiring lives on logic_relay, logic_auto and
    /// logic_auto_citadel entities rather than on the thing being driven.
    /// Read out of dl_example.vmap 2026-08-23.
    ///
    /// Optional and empty for nearly every entity, so plans written before
    /// this field existed still parse unchanged.
    /// </summary>
    [JsonPropertyName("connections")]
    public List<MapConnection> Connections { get; set; } = new();
}

/// <summary>
/// One output-to-input wire, as it appears in a plan.
///
/// TARGETNAME IS A STRING, and that is the whole reason connections are cheap
/// here: nothing is referenced, so nothing needs an id, and a mirrored twin
/// only needs its target string prefixed the same way every other name is.
///
/// Every field has the value observed in all 89 of dl_example's connections
/// as its default, so a plan usually only sets OutputName, TargetName and
/// InputName.
/// </summary>
public sealed class MapConnection
{
    [JsonPropertyName("outputName")]
    public string OutputName { get; set; } = "OnTrigger";

    /// <summary>7 in all 89 observed, across six owner classnames.</summary>
    [JsonPropertyName("targetType")]
    public int TargetType { get; set; } = 7;

    [JsonPropertyName("targetName")]
    public string TargetName { get; set; } = "";

    [JsonPropertyName("inputName")]
    public string InputName { get; set; } = "Enable";

    /// <summary>Empty in all 89, but always present.</summary>
    [JsonPropertyName("overrideParam")]
    public string OverrideParam { get; set; } = "";

    [JsonPropertyName("delay")]
    public double Delay { get; set; } = 0;

    /// <summary>-1 is unlimited, and is the value in all 89.</summary>
    [JsonPropertyName("timesToFire")]
    public int TimesToFire { get; set; } = -1;
}

/// <summary>
/// A path. Its keyvalues say WHAT it is (lanenum, LaneSlot for a lane;
/// lane_number, radius, effect_name for a zipline); its Nodes say where it
/// goes. Order is the route order.
/// </summary>
public sealed class MapPath
{
    [JsonPropertyName("name")]
    public string? Name { get; set; }

    [JsonPropertyName("classname")]
    public string ClassName { get; set; } = "lane_marker_path";

    /// <summary>Where the path's own widget sits. Nodes carry world positions
    /// of their own and are NOT relative to this.</summary>
    [JsonPropertyName("origin")]
    public double[] Origin { get; set; } = { 0, 0, 0 };

    [JsonPropertyName("angles")]
    public double[] Angles { get; set; } = { 0, 0, 0 };

    [JsonPropertyName("properties")]
    public Dictionary<string, string> Properties { get; set; } = new();

    /// <summary>1 everywhere in dl_example.</summary>
    [JsonPropertyName("interpolation_type")]
    public int InterpolationType { get; set; } = 1;

    [JsonPropertyName("closed_loop")]
    public bool ClosedLoop { get; set; }

    [JsonPropertyName("particle_snapshot_spacing")]
    public double ParticleSnapshotSpacing { get; set; } = 16;

    [JsonPropertyName("nodes")]
    public List<MapPathNode> Nodes { get; set; } = new();
}

/// <summary>
/// One control point. A path_node_generic in a trooper lane carries no
/// keyvalues at all; a citadel_zipline_path_node carries a dozen.
/// </summary>
public sealed class MapPathNode
{
    [JsonPropertyName("classname")]
    public string ClassName { get; set; } = "path_node_generic";

    [JsonPropertyName("origin")]
    public double[] Origin { get; set; } = { 0, 0, 0 };

    [JsonPropertyName("angles")]
    public double[] Angles { get; set; } = { 0, 0, 0 };

    [JsonPropertyName("in_tangent")]
    public double[] InTangent { get; set; } = { 0, 0, 0 };

    [JsonPropertyName("out_tangent")]
    public double[] OutTangent { get; set; } = { 0, 0, 0 };

    [JsonPropertyName("in_tangent_type")]
    public int InTangentType { get; set; } = 1;

    [JsonPropertyName("out_tangent_type")]
    public int OutTangentType { get; set; } = 1;

    [JsonPropertyName("properties")]
    public Dictionary<string, string> Properties { get; set; } = new();
}
