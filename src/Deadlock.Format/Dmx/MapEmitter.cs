using System;
using System.Collections.Generic;
using System.Globalization;

namespace Deadlock.Format.Dmx;

/// <summary>Emitter input. Kept local to Format so this layer takes no new
/// project reference; the CLI maps MapPlan onto these.</summary>
public sealed class BoxSpec
{
    public double[] Origin = { 0, 0, 0 };
    public double[] Extents = { 64, 64, 64 };
    public double[] Angles = { 0, 0, 0 };
    public string Material = "materials/dev/reflectivity_30.vmat";
}

public sealed class EntitySpec
{
    public string ClassName = "info_team_spawn";
    public double[] Origin = { 0, 0, 0 };
    public double[] Angles = { 0, 0, 0 };
    public Dictionary<string, string> Properties = new(StringComparer.Ordinal);
}

/// <summary>
/// One control point on a path. Position is WORLD space, like an entity's,
/// not local to the path: dl_example's CMapPathNode carries a full world
/// origin and the parent CMapPath's own origin is just where its widget sits.
/// </summary>
public sealed class PathNodeSpec
{
    public string ClassName = "path_node_generic";
    public double[] Origin = { 0, 0, 0 };
    public double[] Angles = { 0, 0, 0 };
    public double[] InTangent = { 0, 0, 0 };
    public double[] OutTangent = { 0, 0, 0 };
    public int InTangentType = 1;
    public int OutTangentType = 1;
    public Dictionary<string, string> Properties = new(StringComparer.Ordinal);
}

/// <summary>
/// A path: a spline the game follows. A lane_marker_path is what troopers
/// walk; a citadel_zipline_path is the same structure with a different
/// classname and keyvalues.
///
/// WHY THE NODES ARE INLINE HERE AND REFERENCED IN dl_example. In the real
/// map every root-level element is listed BOTH in CMapWorld's children and
/// in CVisibilityMgr's nodes array. Two references means dmxconvert must
/// hoist the element to top level and point at it by id, which is where 767
/// of the 767 ids in that file come from. This emitter leaves
/// CVisibilityMgr's nodes empty, exactly as it already does for meshes and
/// entities, so each node is referenced ONCE and stays inline. The no-GUID
/// property survives.
///
/// UNCONFIRMED: whether Deadlock or Hammer requires path nodes to be
/// registered in CVisibilityMgr. The sealed room loads with that array empty
/// for meshes and entities, which is the evidence this rests on, and it is
/// not proof for paths. If a compile or a load rejects the file, populating
/// CVisibilityMgr is hypothesis #1 — and doing so forces ids back in.
/// </summary>
public sealed class PathSpec
{
    public string ClassName = "lane_marker_path";
    public double[] Origin = { 0, 0, 0 };
    public double[] Angles = { 0, 0, 0 };
    public Dictionary<string, string> Properties = new(StringComparer.Ordinal);
    /// <summary>1 in every path in dl_example. Read off, not chosen.</summary>
    public int InterpolationType = 1;
    public bool ClosedLoop = false;
    public double ParticleSnapshotSpacing = 16;
    public List<PathNodeSpec> Nodes = new();
}

/// <summary>
/// Builds a CMapRootElement document from boxes and point entities.
///
/// WHY THERE ARE NO GUIDS HERE. keyvalues2_noids writes an element id only
/// where an element is referenced MORE THAN ONCE (measured: 767 ids for 768
/// multiply-referenced elements in dl_example.vmap). Everything this emitter
/// produces is referenced exactly once, so the document needs no ids at all.
/// Adding groups, selection sets, paths or entity connections would break
/// that property and reintroduce id generation. Weigh it before extending.
///
/// Structural values (editorbuild, editorversion, the empty CMapVariableSet,
/// the CMapWorld defaults) are copied from the fixture, not invented.
/// </summary>
public static class MapEmitter
{
    private static string F(double d)
        => d.ToString("R", CultureInfo.InvariantCulture);

    private static DmxValue S(string type, string v) => DmxValue.OfScalar(type, v);
    private static DmxValue Int(int v) => S("int", v.ToString(CultureInfo.InvariantCulture));
    private static DmxValue Flt(double v) => S("float", F(v));
    private static DmxValue Bool(bool v) => S("bool", v ? "1" : "0");
    private static DmxValue Str(string v) => S("string", v);
    private static DmxValue NullEl() => S("element", "");
    private static DmxValue V3(double[] v) => S("vector3", $"{F(v[0])} {F(v[1])} {F(v[2])}");
    private static DmxValue Ang(double[] v) => S("qangle", $"{F(v[0])} {F(v[1])} {F(v[2])}");

    private static DmxValue EmptyArray(string type)
        => DmxValue.OfArray(type, Array.Empty<DmxItem>());

    private static DmxValue IntArray(IEnumerable<int> xs)
    {
        var items = new List<DmxItem>();
        foreach (var x in xs) items.Add(DmxItem.Scalar(x.ToString(CultureInfo.InvariantCulture)));
        return DmxValue.OfArray("int_array", items);
    }

    private static DmxValue Vec3Array(IEnumerable<double[]> xs)
    {
        var items = new List<DmxItem>();
        foreach (var v in xs) items.Add(DmxItem.Scalar($"{F(v[0])} {F(v[1])} {F(v[2])}"));
        return DmxValue.OfArray("vector3_array", items);
    }

    private static DmxValue Vec2Array(IEnumerable<double[]> xs)
    {
        var items = new List<DmxItem>();
        foreach (var v in xs) items.Add(DmxItem.Scalar($"{F(v[0])} {F(v[1])}"));
        return DmxValue.OfArray("vector2_array", items);
    }

    private static DmxValue Vec4Array(IEnumerable<double[]> xs)
    {
        var items = new List<DmxItem>();
        foreach (var v in xs) items.Add(DmxItem.Scalar($"{F(v[0])} {F(v[1])} {F(v[2])} {F(v[3])}"));
        return DmxValue.OfArray("vector4_array", items);
    }

    private static DmxValue StringArray(IEnumerable<string> xs)
    {
        var items = new List<DmxItem>();
        foreach (var s in xs) items.Add(DmxItem.Scalar(s));
        return DmxValue.OfArray("string_array", items);
    }

    private static DmxValue InlineArray(IEnumerable<DmxElement> els)
    {
        var items = new List<DmxItem>();
        foreach (var e in els) items.Add(DmxItem.Inline(e));
        return DmxValue.OfArray("element_array", items);
    }

    public static DmxDocument Emit(IReadOnlyList<BoxSpec> boxes,
                                   IReadOnlyList<EntitySpec> entities)
        => Emit(boxes, entities, Array.Empty<PathSpec>());

    public static DmxDocument Emit(IReadOnlyList<BoxSpec> boxes,
                                   IReadOnlyList<EntitySpec> entities,
                                   IReadOnlyList<PathSpec> paths)
    {
        var doc = new DmxDocument("keyvalues2_noids", 4, "vmap", 40);

        // nodeID is a plain counter shared across every node type. A path
        // and its nodes each take one, so the ids stay unique document-wide.
        var nodeId = 1;
        var children = new List<DmxElement>();
        foreach (var b in boxes) children.Add(MapMesh(b, ++nodeId));
        foreach (var e in entities) children.Add(MapEntity(e, ++nodeId));
        foreach (var p in paths) children.Add(MapPath(p, ref nodeId));

        var world = new DmxElement("CMapWorld");
        world.Set("nodeID", Int(1));
        world.Set("referenceID", S("uint64", "0x0"));
        world.Set("children", InlineArray(children));
        world.Set("variableTargetKeys", EmptyArray("string_array"));
        world.Set("variableNames", EmptyArray("string_array"));
        world.Set("relayPlugData", DmxValue.OfInline("DmePlugList", PlugList()));
        world.Set("connectionsData", EmptyArray("element_array"));
        world.Set("entity_properties",
            DmxValue.OfInline("EditGameClassProps", ClassProps("worldspawn", null)));
        world.Set("nextDecalID", Int(0));
        world.Set("fixupEntityNames", Bool(true));
        world.Set("mapUsageType", Str("standard"));
        world.Set("origin", V3(new double[] { 0, 0, 0 }));
        world.Set("angles", Ang(new double[] { 0, 0, 0 }));
        world.Set("scales", V3(new double[] { 1, 1, 1 }));
        world.Set("transformLocked", Bool(false));
        world.Set("force_hidden", Bool(false));
        world.Set("editorOnly", Bool(false));

        var vis = new DmxElement("CVisibilityMgr");
        vis.Set("nodeID", Int(0));
        vis.Set("referenceID", S("uint64", "0x0"));
        vis.Set("children", EmptyArray("element_array"));
        vis.Set("variableTargetKeys", EmptyArray("string_array"));
        vis.Set("variableNames", EmptyArray("string_array"));
        vis.Set("nodes", EmptyArray("element_array"));
        vis.Set("hiddenFlags", EmptyArray("int_array"));
        vis.Set("origin", V3(new double[] { 0, 0, 0 }));
        vis.Set("angles", Ang(new double[] { 0, 0, 0 }));
        vis.Set("scales", V3(new double[] { 1, 1, 1 }));
        vis.Set("transformLocked", Bool(false));
        vis.Set("force_hidden", Bool(false));
        vis.Set("editorOnly", Bool(false));

        var vars = new DmxElement("CMapVariableSet");
        vars.Set("variableNames", EmptyArray("string_array"));
        vars.Set("variableValues", EmptyArray("string_array"));
        vars.Set("variableTypeNames", EmptyArray("string_array"));
        vars.Set("variableTypeParameters", EmptyArray("string_array"));
        vars.Set("m_ChoiceGroups", EmptyArray("element_array"));

        var sel = new DmxElement("CMapSelectionSet");
        sel.Set("children", EmptyArray("element_array"));
        sel.Set("selectionSetName", Str(""));
        sel.Set("selectionSetData", NullEl());

        var cams = new DmxElement("CStoredCameras");
        cams.Set("activecamera", Int(-1));
        cams.Set("cameras", EmptyArray("element_array"));

        var root = new DmxElement("CMapRootElement");
        root.Set("isprefab", Bool(false));
        // Copied from the fixture. If the compiler or Hammer ever rejects the
        // file, schema drift on these two is hypothesis #1.
        root.Set("editorbuild", Int(10169));
        root.Set("editorversion", Int(400));
        root.Set("itemFile", Str(""));
        root.Set("defaultcamera", NullEl());
        root.Set("3dcameras", DmxValue.OfInline("CStoredCameras", cams));
        root.Set("world", DmxValue.OfInline("CMapWorld", world));
        root.Set("visbility", DmxValue.OfInline("CVisibilityMgr", vis)); // sic
        root.Set("mapVariables", DmxValue.OfInline("CMapVariableSet", vars));
        root.Set("rootSelectionSet", DmxValue.OfInline("CMapSelectionSet", sel));
        root.Set("m_ReferencedMeshSnapshots", EmptyArray("element_array"));
        root.Set("m_bIsCordoning", Bool(false));
        root.Set("m_bCordonsVisible", Bool(false));
        root.Set("nodeInstanceData", EmptyArray("element_array"));

        doc.Roots.Add(root);
        return doc;
    }

    private static DmxElement PlugList()
    {
        var p = new DmxElement("DmePlugList");
        p.Set("names", EmptyArray("string_array"));
        p.Set("dataTypes", EmptyArray("int_array"));
        p.Set("plugTypes", EmptyArray("int_array"));
        p.Set("descriptions", EmptyArray("string_array"));
        return p;
    }

    private static DmxElement ClassProps(string className, IEnumerable<KeyValuePair<string, string>>? extra)
    {
        var e = new DmxElement("EditGameClassProps");
        e.Set("classname", Str(className));
        if (extra is null) return e;
        foreach (var (k, v) in extra)
        {
            if (k == "classname") continue;
            e.Set(k, Str(v));
        }
        return e;
    }

    private static DmxElement MapEntity(EntitySpec spec, int nodeId)
    {
        var e = new DmxElement("CMapEntity");
        e.Set("nodeID", Int(nodeId));
        e.Set("referenceID", S("uint64", "0x0"));
        e.Set("children", EmptyArray("element_array"));
        e.Set("variableTargetKeys", EmptyArray("string_array"));
        e.Set("variableNames", EmptyArray("string_array"));
        e.Set("relayPlugData", DmxValue.OfInline("DmePlugList", PlugList()));
        e.Set("connectionsData", EmptyArray("element_array"));
        e.Set("entity_properties",
            DmxValue.OfInline("EditGameClassProps", ClassProps(spec.ClassName, spec.Properties)));
        e.Set("hitNormal", V3(new double[] { 0, 0, 1 }));
        e.Set("isProceduralEntity", Bool(false));
        e.Set("origin", V3(spec.Origin));
        e.Set("angles", Ang(spec.Angles));
        e.Set("scales", V3(new double[] { 1, 1, 1 }));
        e.Set("transformLocked", Bool(false));
        e.Set("force_hidden", Bool(false));
        e.Set("editorOnly", Bool(false));
        return e;
    }

    /// <summary>
    /// A CMapPath holding its CMapPathNode children inline. Attribute set and
    /// order are copied from a real lane_marker_path in dl_example.vmap, read
    /// verbatim, not inferred.
    /// </summary>
    private static DmxElement MapPath(PathSpec spec, ref int nodeId)
    {
        var e = new DmxElement("CMapPath");
        e.Set("nodeID", Int(++nodeId));
        e.Set("referenceID", S("uint64", "0x0"));

        var nodes = new List<DmxElement>();
        foreach (var n in spec.Nodes) nodes.Add(MapPathNode(n, ++nodeId));
        e.Set("children", InlineArray(nodes));

        e.Set("variableTargetKeys", EmptyArray("string_array"));
        e.Set("variableNames", EmptyArray("string_array"));
        e.Set("relayPlugData", DmxValue.OfInline("DmePlugList", PlugList()));
        e.Set("connectionsData", EmptyArray("element_array"));
        e.Set("entity_properties",
            DmxValue.OfInline("EditGameClassProps", ClassProps(spec.ClassName, spec.Properties)));
        e.Set("hitNormal", V3(new double[] { 0, 0, 1 }));
        e.Set("isProceduralEntity", Bool(false));
        e.Set("origin", V3(spec.Origin));
        e.Set("angles", Ang(spec.Angles));
        e.Set("scales", V3(new double[] { 1, 1, 1 }));
        e.Set("transformLocked", Bool(false));
        e.Set("force_hidden", Bool(false));
        e.Set("editorOnly", Bool(false));
        e.Set("interpolationType", Int(spec.InterpolationType));
        e.Set("closedLoop", Bool(spec.ClosedLoop));
        e.Set("particleSnapshotSpacing", Flt(spec.ParticleSnapshotSpacing));
        return e;
    }

    /// <summary>
    /// A CMapPathNode. Same shape as a CMapEntity plus the four tangent
    /// attributes. A path_node_generic carries NO keyvalues beyond its
    /// classname in dl_example — the position is the whole content.
    /// </summary>
    private static DmxElement MapPathNode(PathNodeSpec spec, int nodeId)
    {
        var e = new DmxElement("CMapPathNode");
        e.Set("nodeID", Int(nodeId));
        e.Set("referenceID", S("uint64", "0x0"));
        e.Set("children", EmptyArray("element_array"));
        e.Set("variableTargetKeys", EmptyArray("string_array"));
        e.Set("variableNames", EmptyArray("string_array"));
        e.Set("relayPlugData", DmxValue.OfInline("DmePlugList", PlugList()));
        e.Set("connectionsData", EmptyArray("element_array"));
        e.Set("entity_properties",
            DmxValue.OfInline("EditGameClassProps", ClassProps(spec.ClassName, spec.Properties)));
        e.Set("hitNormal", V3(new double[] { 0, 0, 1 }));
        e.Set("isProceduralEntity", Bool(false));
        e.Set("origin", V3(spec.Origin));
        e.Set("angles", Ang(spec.Angles));
        e.Set("scales", V3(new double[] { 1, 1, 1 }));
        e.Set("transformLocked", Bool(false));
        e.Set("force_hidden", Bool(false));
        e.Set("editorOnly", Bool(false));
        e.Set("inTangent", V3(spec.InTangent));
        e.Set("outTangent", V3(spec.OutTangent));
        e.Set("inTangentType", Int(spec.InTangentType));
        e.Set("outTangentType", Int(spec.OutTangentType));
        return e;
    }

    private static DmxElement MapMesh(BoxSpec spec, int nodeId)
    {
        var e = new DmxElement("CMapMesh");
        e.Set("nodeID", Int(nodeId));
        e.Set("referenceID", S("uint64", "0x0"));
        e.Set("children", EmptyArray("element_array"));
        e.Set("variableTargetKeys", EmptyArray("string_array"));
        e.Set("variableNames", EmptyArray("string_array"));
        e.Set("cubeMapName", Str(""));
        e.Set("visexclude", Bool(false));
        e.Set("disablemerging", Bool(false));
        e.Set("renderwithdynamic", Bool(false));
        e.Set("disableHeightDisplacement", Bool(false));
        e.Set("fademindist", Flt(-1));
        e.Set("fademaxdist", Flt(0));
        e.Set("bakelighting", Bool(true));
        e.Set("renderToCubemaps", Bool(true));
        e.Set("emissiveLightingEnabled", Bool(true));
        e.Set("emissiveLightingBoost", Flt(1));
        e.Set("disableShadows", Int(0));
        e.Set("lightingDummy", Bool(false));
        e.Set("keep_vertices", Bool(false));
        e.Set("smoothingAngle", Flt(180));
        e.Set("tintColor", S("color", "255 255 255 255"));
        e.Set("renderAmt", Int(255));
        e.Set("physicsType", Str("default"));
        e.Set("physicsGroup", Str(""));
        e.Set("physicsInteractsAs", Str(""));
        e.Set("physicsInteractsWith", Str(""));
        e.Set("physicsInteractsExclude", Str(""));
        e.Set("meshData", DmxValue.OfInline("CDmePolygonMesh", PolygonMesh(spec)));
        e.Set("origin", V3(spec.Origin));
        e.Set("angles", Ang(spec.Angles));
        e.Set("scales", V3(new double[] { 1, 1, 1 }));
        e.Set("transformLocked", Bool(false));
        e.Set("force_hidden", Bool(false));
        e.Set("editorOnly", Bool(false));
        return e;
    }

    private static DmxElement Stream(string semantic, int dataStateFlags, DmxValue data)
    {
        var s = new DmxElement("CDmePolygonMeshDataStream");
        s.Set("standardAttributeName", Str(semantic));
        s.Set("semanticName", Str(semantic));
        s.Set("semanticIndex", Int(0));
        s.Set("vertexBufferLocation", Int(0));
        s.Set("dataStateFlags", Int(dataStateFlags));
        s.Set("subdivisionBinding", NullEl());
        s.Set("data", data);
        return s;
    }

    private static DmxElement DataArray(int size, params DmxElement[] streams)
    {
        var a = new DmxElement("CDmePolygonMeshDataArray");
        a.Set("size", Int(size));
        a.Set("streams", InlineArray(streams));
        return a;
    }

    private static DmxElement PolygonMesh(BoxSpec spec)
    {
        var (m, positions) = HalfEdgeMesh.Box(spec.Extents[0], spec.Extents[1], spec.Extents[2]);

        var nHalf = m.HalfEdgeCount;
        var nFace = m.FaceCount;

        // Per half-edge attributes. Normals are per FACE but stored per
        // half-edge, so each loop member repeats its face normal.
        var normals = new double[nHalf][];
        var texcoords = new double[nHalf][];
        var tangents = new double[nHalf][];

        var faceNormals = new double[nFace][];
        var axisU = new double[nFace][];
        var axisV = new double[nFace][];

        for (var f = 0; f < nFace; f++)
        {
            var n = FaceNormal(m, positions, f);
            faceNormals[f] = n;
            var (u, v) = ProjectionAxes(n);
            axisU[f] = new[] { u[0], u[1], u[2], 0.0 };
            axisV[f] = new[] { v[0], v[1], v[2], 0.0 };

            var start = m.FaceEdgeIndices[f];
            var h = start;
            do
            {
                normals[h] = n;
                tangents[h] = new[] { u[0], u[1], u[2], -1.0 };
                var p = positions[m.EdgeVertexIndices[h]];
                // 0.25 units per texel matches the fixture's textureScale.
                texcoords[h] = new[]
                {
                    (p[0] * u[0] + p[1] * u[1] + p[2] * u[2]) * 0.25,
                    (p[0] * v[0] + p[1] * v[1] + p[2] * v[2]) * 0.25,
                };
                h = m.EdgeNextIndices[h];
            } while (h != start);
        }

        var mesh = new DmxElement("CDmePolygonMesh");
        mesh.Set("vertexEdgeIndices", IntArray(m.VertexEdgeIndices));
        mesh.Set("vertexDataIndices", IntArray(m.VertexDataIndices));
        mesh.Set("edgeVertexIndices", IntArray(m.EdgeVertexIndices));
        mesh.Set("edgeOppositeIndices", IntArray(m.EdgeOppositeIndices()));
        mesh.Set("edgeNextIndices", IntArray(m.EdgeNextIndices));
        mesh.Set("edgeFaceIndices", IntArray(m.EdgeFaceIndices));
        mesh.Set("edgeDataIndices", IntArray(m.EdgeDataIndices()));
        mesh.Set("edgeVertexDataIndices", IntArray(m.EdgeVertexDataIndices()));
        mesh.Set("faceEdgeIndices", IntArray(m.FaceEdgeIndices));
        mesh.Set("faceDataIndices", IntArray(m.FaceDataIndices()));
        mesh.Set("materials", StringArray(new[] { spec.Material }));

        mesh.Set("vertexData", DmxValue.OfInline("CDmePolygonMeshDataArray",
            DataArray(m.VertexCount, Stream("position", 3, Vec3Array(positions)))));

        mesh.Set("faceVertexData", DmxValue.OfInline("CDmePolygonMeshDataArray",
            DataArray(nHalf,
                Stream("texcoord", 1, Vec2Array(texcoords)),
                Stream("normal", 1, Vec3Array(normals)),
                Stream("tangent", 1, Vec4Array(tangents)))));

        var edgeFlags = new int[m.EdgeCount];
        mesh.Set("edgeData", DmxValue.OfInline("CDmePolygonMeshDataArray",
            DataArray(m.EdgeCount, Stream("flags", 3, IntArray(edgeFlags)))));

        var scale = new List<double[]>();
        var mat = new int[nFace];
        var flags = new int[nFace];
        var lm = new int[nFace];
        for (var f = 0; f < nFace; f++) scale.Add(new[] { 0.25, 0.25 });

        mesh.Set("faceData", DmxValue.OfInline("CDmePolygonMeshDataArray",
            DataArray(nFace,
                Stream("textureScale", 0, Vec2Array(scale)),
                Stream("textureAxisU", 0, Vec4Array(axisU)),
                Stream("textureAxisV", 0, Vec4Array(axisV)),
                Stream("materialindex", 8, IntArray(mat)),
                Stream("flags", 3, IntArray(flags)),
                Stream("lightmapScaleBias", 1, IntArray(lm)))));

        var sub = new DmxElement("CDmePolygonMeshSubdivisionData");
        sub.Set("subdivisionLevels", IntArray(new int[nHalf]));
        sub.Set("streams", EmptyArray("element_array"));
        mesh.Set("subdivisionData", DmxValue.OfInline("CDmePolygonMeshSubdivisionData", sub));

        return mesh;
    }

    private static double[] FaceNormal(HalfEdgeMesh m, double[][] pos, int f)
    {
        // Newell's method: correct for any planar loop, and does not care
        // which three vertices happen to be collinear.
        double nx = 0, ny = 0, nz = 0;
        var start = m.FaceEdgeIndices[f];
        var h = start;
        do
        {
            var a = pos[m.EdgeVertexIndices[h]];
            var next = m.EdgeNextIndices[h];
            var b = pos[m.EdgeVertexIndices[next]];
            nx += (a[1] - b[1]) * (a[2] + b[2]);
            ny += (a[2] - b[2]) * (a[0] + b[0]);
            nz += (a[0] - b[0]) * (a[1] + b[1]);
            h = next;
        } while (h != start);

        var len = Math.Sqrt(nx * nx + ny * ny + nz * nz);
        if (len < 1e-12) return new double[] { 0, 0, 1 };
        return new[] { nx / len, ny / len, nz / len };
    }

    /// <summary>
    /// Source-style projection axes chosen by the dominant normal component.
    /// textureAxisU/V are 4-vectors: axis plus offset, not per-vertex UVs.
    /// </summary>
    private static (double[] u, double[] v) ProjectionAxes(double[] n)
    {
        var ax = Math.Abs(n[0]); var ay = Math.Abs(n[1]); var az = Math.Abs(n[2]);
        if (az >= ax && az >= ay)
            return (new double[] { 1, 0, 0 }, new double[] { 0, -1, 0 });
        if (ax >= ay)
            return (new double[] { 0, 1, 0 }, new double[] { 0, 0, -1 });
        return (new double[] { 1, 0, 0 }, new double[] { 0, 0, -1 });
    }
}