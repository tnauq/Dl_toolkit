using System;
using System.Collections.Generic;

namespace Deadlock.Format.Dmx;

/// <summary>
/// Builds the half-edge index arrays a CDmePolygonMesh needs, from a plain
/// list of faces given as vertex-index loops.
///
/// CONVENTIONS, all read off the smallest mesh in dl_example.vmap (a single
/// quad: 4 verts, 8 half-edges, 1 face) rather than inferred:
///
///   vertexEdgeIndices   [0,2,4,6]         one OUTGOING half-edge per vertex
///   edgeVertexIndices   [1,0,2,1,3,2,0,3] the DESTINATION vertex of each
///   edgeOppositeIndices [1,0,3,2,5,4,7,6] twins live at ADJACENT indices,
///                                         so this is 2k&lt;-&gt;2k+1, derivable
///   edgeNextIndices     [2,7,4,1,6,3,0,5] next half-edge around the loop
///   edgeFaceIndices     [0,-1,0,-1,...]   -1 means the VOID side
///   edgeDataIndices     [0,0,1,1,2,2,3,3] twins share ONE edge record
///   edgeVertexDataIndices [0..7]          per HALF-EDGE, not per edge
///   faceEdgeIndices     [6]               ONE starting half-edge per face;
///                                         the loop is recovered via next
///   faceDataIndices     [0]               per face
///
/// Two granularities are easy to conflate: edgeData is per EDGE (half the
/// half-edge count) while faceVertexData is per HALF-EDGE.
///
/// A quad has four -1 entries because it is an open surface. A SEALED BOX has
/// a real face on both sides of every edge and therefore NO -1 at all. That
/// difference is the cheapest sanity check on a box: <see cref="IsClosed"/>.
/// </summary>
public sealed class HalfEdgeMesh
{
    private readonly Dictionary<(int, int), int> _edgeIds = new();

    private HalfEdgeMesh(int vertexCount)
    {
        VertexCount = vertexCount;
        VertexEdgeIndices = new int[vertexCount];
        for (var i = 0; i < vertexCount; i++) VertexEdgeIndices[i] = -1;
        VertexDataIndices = new int[vertexCount];
        for (var i = 0; i < vertexCount; i++) VertexDataIndices[i] = i;
    }

    public int VertexCount { get; }
    public int EdgeCount => _edgeIds.Count;
    public int HalfEdgeCount => EdgeCount * 2;
    public int FaceCount => FaceEdgeIndices.Count;

    public int[] VertexEdgeIndices { get; }
    public int[] VertexDataIndices { get; }

    public List<int> EdgeVertexIndices { get; } = new();
    public List<int> EdgeNextIndices { get; } = new();
    public List<int> EdgeFaceIndices { get; } = new();
    public List<int> FaceEdgeIndices { get; } = new();

    /// <summary>Twins are adjacent, so this is fully determined.</summary>
    public int[] EdgeOppositeIndices()
    {
        var a = new int[HalfEdgeCount];
        for (var i = 0; i < HalfEdgeCount; i++) a[i] = i ^ 1;
        return a;
    }

    /// <summary>Twins share one edge record.</summary>
    public int[] EdgeDataIndices()
    {
        var a = new int[HalfEdgeCount];
        for (var i = 0; i < HalfEdgeCount; i++) a[i] = i / 2;
        return a;
    }

    /// <summary>Per half-edge, identity.</summary>
    public int[] EdgeVertexDataIndices()
    {
        var a = new int[HalfEdgeCount];
        for (var i = 0; i < HalfEdgeCount; i++) a[i] = i;
        return a;
    }

    public int[] FaceDataIndices()
    {
        var a = new int[FaceCount];
        for (var i = 0; i < FaceCount; i++) a[i] = i;
        return a;
    }

    /// <summary>No half-edge on the void side. True for a sealed solid.</summary>
    public bool IsClosed
    {
        get
        {
            foreach (var f in EdgeFaceIndices) if (f < 0) return false;
            return true;
        }
    }

    /// <summary>
    /// The face loops each half-edge belongs to, for verification. Walks
    /// edgeNextIndices and returns false if any loop fails to close or
    /// visits a half-edge twice.
    /// </summary>
    public bool LoopsClose()
    {
        for (var f = 0; f < FaceCount; f++)
        {
            var start = FaceEdgeIndices[f];
            var h = start;
            var guard = 0;
            do
            {
                if (h < 0 || h >= HalfEdgeCount) return false;
                if (EdgeFaceIndices[h] != f) return false;
                h = EdgeNextIndices[h];
                if (++guard > HalfEdgeCount) return false;
            } while (h != start);
        }
        return true;
    }

    /// <summary>
    /// Build from faces given as loops of vertex indices, each wound
    /// counter-clockwise when viewed from OUTSIDE the solid.
    /// </summary>
    public static HalfEdgeMesh FromFaces(int vertexCount, IReadOnlyList<int[]> faces)
    {
        var m = new HalfEdgeMesh(vertexCount);

        // Pass one: allocate an edge id per undirected pair, in order of
        // first encounter, so half-edges 2e and 2e+1 are the twin pair.
        foreach (var loop in faces)
        {
            for (var i = 0; i < loop.Length; i++)
            {
                var a = loop[i];
                var b = loop[(i + 1) % loop.Length];
                var key = a < b ? (a, b) : (b, a);
                if (!m._edgeIds.ContainsKey(key))
                    m._edgeIds[key] = m._edgeIds.Count;
            }
        }

        var n = m.HalfEdgeCount;
        for (var i = 0; i < n; i++)
        {
            m.EdgeVertexIndices.Add(-1);
            m.EdgeNextIndices.Add(-1);
            m.EdgeFaceIndices.Add(-1);
        }

        // Pass two: wire each face loop.
        for (var f = 0; f < faces.Count; f++)
        {
            var loop = faces[f];
            var hes = new int[loop.Length];
            for (var i = 0; i < loop.Length; i++)
            {
                var a = loop[i];
                var b = loop[(i + 1) % loop.Length];
                hes[i] = m.HalfEdge(a, b);
                // edgeVertexIndices holds the DESTINATION vertex.
                m.EdgeVertexIndices[hes[i]] = b;
                m.EdgeFaceIndices[hes[i]] = f;
                if (m.VertexEdgeIndices[a] < 0) m.VertexEdgeIndices[a] = hes[i];
            }
            for (var i = 0; i < hes.Length; i++)
                m.EdgeNextIndices[hes[i]] = hes[(i + 1) % hes.Length];

            // The fixture stores the LAST half-edge of the loop, not the
            // first. Any member is valid; matching it keeps diffs small.
            m.FaceEdgeIndices.Add(hes[^1]);
        }

        // Any twin never claimed by a face is a boundary half-edge. It still
        // needs a destination so the void loop is traversable.
        for (var e = 0; e < m.EdgeCount; e++)
        {
            for (var s = 0; s < 2; s++)
            {
                var h = e * 2 + s;
                if (m.EdgeVertexIndices[h] >= 0) continue;
                var twin = h ^ 1;
                // Destination of a boundary half-edge is the ORIGIN of its
                // twin, which is the destination of the twin's predecessor.
                m.EdgeVertexIndices[h] = m.OriginOf(twin);
            }
        }

        // Boundary loops: link each unclaimed half-edge to the next one
        // around the hole. Not exercised by a sealed box, but a wrong value
        // here would be silent, so it is filled rather than left at -1.
        for (var h = 0; h < n; h++)
        {
            if (m.EdgeFaceIndices[h] >= 0) continue;
            var scan = h ^ 1;
            var guard = 0;
            while (true)
            {
                var prev = m.EdgeNextIndices[scan];
                if (prev < 0) break;
                if (m.EdgeFaceIndices[prev ^ 1] < 0) { m.EdgeNextIndices[h] = prev ^ 1; break; }
                scan = prev;
                if (++guard > n) break;
            }
        }

        return m;
    }

    private int OriginOf(int h)
    {
        var e = h / 2;
        foreach (var (key, id) in _edgeIds)
        {
            if (id != e) continue;
            var (lo, hi) = key;
            var dest = EdgeVertexIndices[h];
            return dest == lo ? hi : lo;
        }
        return -1;
    }

    private int HalfEdge(int a, int b)
    {
        var key = a < b ? (a, b) : (b, a);
        var e = _edgeIds[key];
        return a < b ? e * 2 : e * 2 + 1;
    }

    /// <summary>
    /// An axis-aligned box in LOCAL space, centred on the origin. World
    /// placement is the CMapMesh node's job, so this never needs world
    /// coordinates.
    ///
    /// Vertex order, with h = extents/2:
    ///   0 (-x,-y,-z)  1 (+x,-y,-z)  2 (+x,+y,-z)  3 (-x,+y,-z)
    ///   4 (-x,-y,+z)  5 (+x,-y,+z)  6 (+x,+y,+z)  7 (-x,+y,+z)
    /// Faces wound counter-clockwise seen from outside.
    /// </summary>
    public static (HalfEdgeMesh mesh, double[][] positions) Box(double sx, double sy, double sz)
    {
        var hx = sx / 2; var hy = sy / 2; var hz = sz / 2;
        var p = new[]
        {
            new[] { -hx, -hy, -hz }, new[] { hx, -hy, -hz },
            new[] { hx,  hy, -hz }, new[] { -hx,  hy, -hz },
            new[] { -hx, -hy,  hz }, new[] { hx, -hy,  hz },
            new[] { hx,  hy,  hz }, new[] { -hx,  hy,  hz },
        };

        var faces = new List<int[]>
        {
            new[] { 0, 3, 2, 1 }, // -Z bottom
            new[] { 4, 5, 6, 7 }, // +Z top
            new[] { 0, 1, 5, 4 }, // -Y
            new[] { 2, 3, 7, 6 }, // +Y
            new[] { 1, 2, 6, 5 }, // +X
            new[] { 3, 0, 4, 7 }, // -X
        };

        return (FromFaces(8, faces), p);
    }
}
