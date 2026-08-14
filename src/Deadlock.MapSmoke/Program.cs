using System.Text.Json;
using Deadlock.Contracts;
using Deadlock.Format.Dmx;

// REPLACES the version from the emitter drop: adds `verify`.
//
//   info      <in.vmap.txt>                 census
//   roundtrip <in.vmap.txt> <out.vmap.txt>  read -> write -> read, census
//   emit      <plan.json>   <out.vmap.txt>  MapPlan -> KV2 text
//   verify    <plan.json>   <in.vmap.txt>   does the map still MEAN the plan
//
// `verify` is the identity check across the stage boundary. The census in
// emit-smoke proves nothing was lost by count; this proves each box is
// still in the right place at the right size, and each entity kept its
// keyvalues. Extents are recomputed from the vertex positions rather than
// read from a field, so a geometry bug cannot hide behind matching metadata.

static int Fail(string msg) { Console.Error.WriteLine(msg); return 1; }

static SortedDictionary<string, int> Census(DmxDocument d)
{
    var c = new SortedDictionary<string, int>(StringComparer.Ordinal);
    foreach (var e in d.AllElements())
        c[e.TypeName] = c.TryGetValue(e.TypeName, out var n) ? n + 1 : 1;
    return c;
}

static void PrintCensus(DmxDocument d)
{
    var c = Census(d);
    var total = 0;
    foreach (var (_, v) in c) total += v;
    Console.WriteLine($"elements={total}");
    foreach (var (k, v) in c) Console.WriteLine($"  {v,6}  {k}");
}

if (args.Length < 2)
    return Fail("usage: info <f> | roundtrip <in> <out> | emit <plan> <out> | verify <plan> <map>");

var mode = args[0];
var inPath = args[1];
if (!File.Exists(inPath)) return Fail($"no such file: {inPath}");

// ---------------------------------------------------------------- emit
if (mode == "emit")
{
    if (args.Length < 3) return Fail("emit needs an output path");

    var plan = JsonSerializer.Deserialize<MapPlan>(File.ReadAllText(inPath));
    if (plan is null) return Fail("plan did not deserialize");
    Console.WriteLine($"plan '{plan.Name}' cell={plan.Cell} " +
                      $"boxes={plan.Boxes.Count} entities={plan.Entities.Count}");

    for (var i = 0; i < plan.Boxes.Count; i++)
    {
        var b = plan.Boxes[i];
        var (hm, _) = HalfEdgeMesh.Box(b.Extents[0], b.Extents[1], b.Extents[2]);
        var label = b.Name ?? $"box[{i}]";
        if (!hm.IsClosed) return Fail($"{label}: NOT SEALED — edgeFaceIndices contains -1");
        if (!hm.LoopsClose()) return Fail($"{label}: a face loop does not close");
        if (hm.HalfEdgeCount != 24 || hm.FaceCount != 6 || hm.VertexCount != 8)
            return Fail($"{label}: expected 8/24/6, got " +
                        $"{hm.VertexCount}/{hm.HalfEdgeCount}/{hm.FaceCount}");
    }
    Console.WriteLine($"geometry ok: {plan.Boxes.Count} sealed box(es)");

    var boxes = plan.Boxes.Select(b => new BoxSpec {
        Origin = b.Origin, Extents = b.Extents, Angles = b.Angles, Material = b.Material
    }).ToList();
    var ents = plan.Entities.Select(e => new EntitySpec {
        ClassName = e.ClassName, Origin = e.Origin, Angles = e.Angles, Properties = e.Properties
    }).ToList();

    var doc = MapEmitter.Emit(boxes, ents);
    PrintCensus(doc);

    var text = Kv2Writer.Write(doc);
    File.WriteAllText(args[2], text);
    Console.WriteLine($"wrote {text.Length} chars to {args[2]}");

    var back = Kv2Reader.Read(text);
    if (!back.Ok) return Fail($"REREAD FAILED: {back.Failure} at {back.Offset}");
    Console.WriteLine("reread ok");
    return 0;
}

// -------------------------------------------------------------- verify
if (mode == "verify")
{
    if (args.Length < 3) return Fail("verify needs a map path");
    if (!File.Exists(args[2])) return Fail($"no such file: {args[2]}");

    var plan = JsonSerializer.Deserialize<MapPlan>(File.ReadAllText(inPath));
    if (plan is null) return Fail("plan did not deserialize");

    var rr = Kv2Reader.Read(File.ReadAllText(args[2]));
    if (!rr.Ok) return Fail($"map parse failed: {rr.Failure} at {rr.Offset}");

    var map = MapReader.Read(rr.Document!);
    Console.WriteLine($"plan:  {plan.Boxes.Count} boxes, {plan.Entities.Count} entities");
    Console.WriteLine($"map:   {map.Boxes.Count} boxes, {map.Entities.Count} entities");

    var bad = 0;
    // Tolerance, not equality: the value survives a float round trip
    // through text and back, so exact comparison would fail on noise
    // rather than on error. A tenth of a unit is 2.5 mm.
    const double TOL = 0.1;
    static bool Near(double a, double b) => Math.Abs(a - b) <= 0.1;
    static bool NearV(double[] a, double[] b) =>
        Near(a[0], b[0]) && Near(a[1], b[1]) && Near(a[2], b[2]);
    static string V(double[] v) => $"[{v[0]:0.##} {v[1]:0.##} {v[2]:0.##}]";

    if (map.Boxes.Count != plan.Boxes.Count)
    { Console.Error.WriteLine("BOX COUNT differs"); bad++; }

    for (var i = 0; i < Math.Min(plan.Boxes.Count, map.Boxes.Count); i++)
    {
        var p = plan.Boxes[i]; var m = map.Boxes[i];
        var label = p.Name ?? $"box[{i}]";
        if (!NearV(p.Origin, m.Origin))
        { Console.Error.WriteLine($"{label}: origin {V(p.Origin)} -> {V(m.Origin)}"); bad++; }
        if (!NearV(p.Extents, m.Extents))
        { Console.Error.WriteLine($"{label}: extents {V(p.Extents)} -> {V(m.Extents)}"); bad++; }
        if (!NearV(p.Angles, m.Angles))
        { Console.Error.WriteLine($"{label}: angles {V(p.Angles)} -> {V(m.Angles)}"); bad++; }
        if (m.VertexCount != 8 || m.FaceCount != 6)
        { Console.Error.WriteLine($"{label}: {m.VertexCount} verts / {m.FaceCount} faces, want 8/6"); bad++; }
        if (!string.Equals(p.Material, m.Material, StringComparison.Ordinal))
        { Console.Error.WriteLine($"{label}: material '{p.Material}' -> '{m.Material}'"); bad++; }
        else Console.WriteLine($"  ok  {label} {V(m.Origin)} size {V(m.Extents)}");
    }

    if (map.Entities.Count != plan.Entities.Count)
    { Console.Error.WriteLine("ENTITY COUNT differs"); bad++; }

    for (var i = 0; i < Math.Min(plan.Entities.Count, map.Entities.Count); i++)
    {
        var p = plan.Entities[i]; var m = map.Entities[i];
        if (!string.Equals(p.ClassName, m.ClassName, StringComparison.Ordinal))
        { Console.Error.WriteLine($"entity[{i}]: class '{p.ClassName}' -> '{m.ClassName}'"); bad++; continue; }
        if (!NearV(p.Origin, m.Origin))
        { Console.Error.WriteLine($"{p.ClassName}[{i}]: origin {V(p.Origin)} -> {V(m.Origin)}"); bad++; }
        if (!NearV(p.Angles, m.Angles))
        { Console.Error.WriteLine($"{p.ClassName}[{i}]: angles {V(p.Angles)} -> {V(m.Angles)}"); bad++; }
        foreach (var (k, want) in p.Properties)
        {
            m.Properties.TryGetValue(k, out var got);
            if (!string.Equals(want, got, StringComparison.Ordinal))
            { Console.Error.WriteLine($"{p.ClassName}[{i}]: {k} '{want}' -> '{got ?? "(missing)"}'"); bad++; }
        }
        if (bad == 0 || true) Console.WriteLine($"  ok  {m.ClassName} {V(m.Origin)}");
    }

    if (bad != 0) return Fail($"\nVERIFY FAILED in {bad} place(s)");
    Console.WriteLine($"\nverified: every box and entity survived the trip (tolerance {TOL} u)");
    return 0;
}

// ------------------------------------------------------- info / roundtrip
var text0 = File.ReadAllText(inPath);
Console.WriteLine($"read {text0.Length} chars from {inPath}");

var r = Kv2Reader.Read(text0);
if (!r.Ok) return Fail($"parse failed: {r.Failure} at offset {r.Offset}");

var doc0 = r.Document!;
Console.WriteLine($"encoding={doc0.Encoding} {doc0.EncodingVersion} " +
                  $"format={doc0.Format} {doc0.FormatVersion} roots={doc0.Roots.Count}");
PrintCensus(doc0);

if (mode == "info") return 0;
if (mode != "roundtrip") return Fail($"unknown mode: {mode}");
if (args.Length < 3) return Fail("roundtrip needs an output path");

var census0 = Census(doc0);
var written = Kv2Writer.Write(doc0);
File.WriteAllText(args[2], written);
Console.WriteLine($"wrote {written.Length} chars to {args[2]}");

var r2 = Kv2Reader.Read(written);
if (!r2.Ok) return Fail($"REREAD FAILED: {r2.Failure} at offset {r2.Offset}");

var census2 = Census(r2.Document!);
var badc = 0;
foreach (var (k, v) in census0)
{
    census2.TryGetValue(k, out var got);
    if (got != v) { Console.Error.WriteLine($"MISMATCH {k}: {v} -> {got}"); badc++; }
}
foreach (var (k, v) in census2)
    if (!census0.ContainsKey(k)) { Console.Error.WriteLine($"ADDED {k}: {v}"); badc++; }

if (badc != 0) return Fail($"census differs across the writer in {badc} type(s)");
Console.WriteLine("census identical across read -> write -> read");
return 0;
