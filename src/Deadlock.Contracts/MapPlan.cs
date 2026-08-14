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
}
