using System;
using System.Collections.Generic;
using System.Globalization;

namespace Deadlock.Format.Dmx;

/// <summary>
/// Reads a DMX map document back into boxes and entities, so an emitted
/// .vmap can be compared against the plan it came from.
///
/// This is the OTHER HALF of the identity check the settled decisions call
/// for: "a green export is not a correct export". emit-smoke proves the
/// element census survives; it does not prove the geometry means the same
/// thing. A box whose extents came out half size, or a spawn that lost its
/// teamnumber, would pass a census check untouched.
///
/// Extents are RECOVERED, not read: CDmePolygonMesh stores local-space
/// vertex positions, so the box size is the bounding span of its position
/// stream. That is deliberate — recomputing from the actual geometry is
/// what makes this a check rather than a restatement.
/// </summary>
public static class MapReader
{
    public sealed class ReadBox
    {
        public double[] Origin = { 0, 0, 0 };
        public double[] Extents = { 0, 0, 0 };
        public double[] Angles = { 0, 0, 0 };
        public string Material = "";
        public int VertexCount;
        public int FaceCount;
    }

    public sealed class ReadEntity
    {
        public string ClassName = "";
        public double[] Origin = { 0, 0, 0 };
        public double[] Angles = { 0, 0, 0 };
        public Dictionary<string, string> Properties = new(StringComparer.Ordinal);

        /// <summary>Child geometry of a brush entity, or null.</summary>
        public ReadBox? Mesh;
    }

    public sealed class ReadPathNode
    {
        public string ClassName = "";
        public double[] Origin = { 0, 0, 0 };
        public double[] InTangent = { 0, 0, 0 };
        public double[] OutTangent = { 0, 0, 0 };
        public Dictionary<string, string> Properties = new(StringComparer.Ordinal);
    }

    public sealed class ReadPath
    {
        public string ClassName = "";
        public double[] Origin = { 0, 0, 0 };
        public double[] Angles = { 0, 0, 0 };
        public Dictionary<string, string> Properties = new(StringComparer.Ordinal);
        public List<ReadPathNode> Nodes = new();
    }

    public sealed class ReadMap
    {
        public List<ReadBox> Boxes = new();
        public List<ReadEntity> Entities = new();
        public List<ReadPath> Paths = new();
    }

    private static double[] Vec(string? s, int n)
    {
        var v = new double[n];
        if (string.IsNullOrWhiteSpace(s)) return v;
        var parts = s.Split(' ', StringSplitOptions.RemoveEmptyEntries);
        for (var i = 0; i < n && i < parts.Length; i++)
            double.TryParse(parts[i], NumberStyles.Float,
                            CultureInfo.InvariantCulture, out v[i]);
        return v;
    }

    /// <summary>
    /// One CMapMesh into a ReadBox. Extents are RECOVERED from the vertex
    /// positions, never read from a field, so a geometry bug cannot hide
    /// behind matching metadata.
    /// </summary>
    private static ReadBox ReadMesh(DmxElement el)
    {
        var b = new ReadBox
        {
            Origin = Vec(el.GetScalar("origin"), 3),
            Angles = Vec(el.GetScalar("angles"), 3)
        };

        var mesh = el.Get("meshData")?.Element;
        if (mesh is null) return b;

        var mats = mesh.Get("materials");
        if (mats?.Items is { Count: > 0 })
            b.Material = mats.Items[0].Text ?? "";

        var faces = mesh.Get("faceEdgeIndices");
        b.FaceCount = faces?.Items?.Count ?? 0;

        var pos = FindStream(mesh, "vertexData", "position");
        if (pos is null) return b;

        b.VertexCount = pos.Count;
        double minX = double.MaxValue, minY = double.MaxValue, minZ = double.MaxValue;
        double maxX = double.MinValue, maxY = double.MinValue, maxZ = double.MinValue;
        foreach (var item in pos)
        {
            var p = Vec(item.Text, 3);
            if (p[0] < minX) minX = p[0];
            if (p[1] < minY) minY = p[1];
            if (p[2] < minZ) minZ = p[2];
            if (p[0] > maxX) maxX = p[0];
            if (p[1] > maxY) maxY = p[1];
            if (p[2] > maxZ) maxZ = p[2];
        }
        if (b.VertexCount > 0)
            b.Extents = new[] { maxX - minX, maxY - minY, maxZ - minZ };
        return b;
    }

    public static ReadMap Read(DmxDocument doc)
    {
        var map = new ReadMap();

        // Meshes that belong to an entity, collected first so the main walk
        // can tell a world box from a brush volume.
        var childMeshes = new HashSet<DmxElement>();
        foreach (var el in doc.AllElements())
        {
            if (el.TypeName != "CMapEntity") continue;
            var kids = el.Get("children");
            if (kids?.Items is null) continue;
            foreach (var it in kids.Items)
                if (it.Element is { TypeName: "CMapMesh" } m)
                    childMeshes.Add(m);
        }

        foreach (var el in doc.AllElements())
        {
            if (el.TypeName == "CMapMesh")
            {
                // A CMapMesh that is a CHILD of an entity is that entity's
                // brush volume, not a world box. AllElements() walks into
                // children, so without this the shop volumes would inflate
                // the box count and break the plan-vs-map comparison.
                if (childMeshes.Contains(el)) continue;
                map.Boxes.Add(ReadMesh(el));
            }
            else if (el.TypeName == "CMapPath")
            {
                var p = new ReadPath
                {
                    Origin = Vec(el.GetScalar("origin"), 3),
                    Angles = Vec(el.GetScalar("angles"), 3)
                };
                ReadProps(el, out var pcls, p.Properties);
                p.ClassName = pcls;

                // Nodes are inline in children. Reading them back in order is
                // the only way to prove the ROUTE survived, as opposed to the
                // path element merely existing.
                var kids = el.Get("children");
                if (kids?.Items is not null)
                {
                    foreach (var it in kids.Items)
                    {
                        var n = it.Element;
                        if (n is null || n.TypeName != "CMapPathNode") continue;
                        var rn = new ReadPathNode
                        {
                            Origin = Vec(n.GetScalar("origin"), 3),
                            InTangent = Vec(n.GetScalar("inTangent"), 3),
                            OutTangent = Vec(n.GetScalar("outTangent"), 3)
                        };
                        ReadProps(n, out var ncls, rn.Properties);
                        rn.ClassName = ncls;
                        p.Nodes.Add(rn);
                    }
                }
                map.Paths.Add(p);
            }
            else if (el.TypeName == "CMapEntity")
            {
                var e = new ReadEntity
                {
                    Origin = Vec(el.GetScalar("origin"), 3),
                    Angles = Vec(el.GetScalar("angles"), 3)
                };
                ReadProps(el, out var ecls, e.Properties);
                e.ClassName = ecls;

                var kids = el.Get("children");
                if (kids?.Items is not null)
                {
                    foreach (var it in kids.Items)
                    {
                        if (it.Element is { TypeName: "CMapMesh" } m)
                        {
                            e.Mesh = ReadMesh(m);
                            break;
                        }
                    }
                }
                map.Entities.Add(e);
            }
        }
        return map;
    }

    /// <summary>
    /// Pull classname and every other scalar out of an element's
    /// entity_properties. Shared by entities, paths and path nodes, which all
    /// carry the same EditGameClassProps bag.
    /// </summary>
    private static void ReadProps(DmxElement el, out string className,
                                  Dictionary<string, string> into)
    {
        className = "";
        var props = el.Get("entity_properties")?.Element;
        if (props is null) return;
        foreach (var (k, v) in props.Attributes)
        {
            if (v.Kind != DmxValueKind.Scalar) continue;
            if (k == "classname") className = v.Scalar ?? "";
            else into[k] = v.Scalar ?? "";
        }
    }

    /// <summary>
    /// Walk mesh -> &lt;arrayName&gt; -> streams -> the stream whose
    /// semanticName matches, and hand back its data items.
    /// </summary>
    private static IReadOnlyList<DmxItem>? FindStream(DmxElement mesh,
                                                      string arrayName,
                                                      string semantic)
    {
        var arr = mesh.Get(arrayName)?.Element;
        var streams = arr?.Get("streams");
        if (streams?.Items is null) return null;

        foreach (var it in streams.Items)
        {
            var s = it.Element;
            if (s is null) continue;
            if (!string.Equals(s.GetScalar("semanticName"), semantic, StringComparison.Ordinal))
                continue;
            return s.Get("data")?.Items;
        }
        return null;
    }
}