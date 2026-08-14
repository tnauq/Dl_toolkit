using System.Text.Json;
using Deadlock.Contracts;
using Deadlock.Format.Dmx;

// REPLACES the version from the 2026-08-14 KV2 drop: adds `emit`.
//
//   info      <in.vmap.txt>                 census
//   roundtrip <in.vmap.txt> <out.vmap.txt>  read -> write -> read, census
//   emit      <plan.json>   <out.vmap.txt>  MapPlan -> KV2 text
//
// `emit` self-checks the geometry before writing: a sealed box must have no
// -1 in edgeFaceIndices and every face loop must close. Those are cheap and
// catch a broken half-edge graph before dmxconvert ever sees it.

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

if (args.Length < 2) return Fail("usage: info <f> | roundtrip <in> <out> | emit <plan> <out>");

var mode = args[0];
var inPath = args[1];
if (!File.Exists(inPath)) return Fail($"no such file: {inPath}");

if (mode == "emit")
{
    if (args.Length < 3) return Fail("emit needs an output path");

    var plan = JsonSerializer.Deserialize<MapPlan>(File.ReadAllText(inPath));
    if (plan is null) return Fail("plan did not deserialize");
    Console.WriteLine($"plan '{plan.Name}' cell={plan.Cell} " +
                      $"boxes={plan.Boxes.Count} entities={plan.Entities.Count}");

    // Geometry self-check, per box, before anything is written.
    for (var i = 0; i < plan.Boxes.Count; i++)
    {
        var b = plan.Boxes[i];
        var (m, _) = HalfEdgeMesh.Box(b.Extents[0], b.Extents[1], b.Extents[2]);
        var label = b.Name ?? $"box[{i}]";
        if (!m.IsClosed)
            return Fail($"{label}: NOT SEALED — edgeFaceIndices contains -1");
        if (!m.LoopsClose())
            return Fail($"{label}: a face loop does not close");
        if (m.HalfEdgeCount != 24 || m.FaceCount != 6 || m.VertexCount != 8)
            return Fail($"{label}: expected 8/24/6, got " +
                        $"{m.VertexCount}/{m.HalfEdgeCount}/{m.FaceCount}");
    }
    Console.WriteLine($"geometry ok: {plan.Boxes.Count} sealed box(es)");

    var boxes = plan.Boxes.Select(b => new BoxSpec
    {
        Origin = b.Origin, Extents = b.Extents, Angles = b.Angles, Material = b.Material
    }).ToList();

    var ents = plan.Entities.Select(e => new EntitySpec
    {
        ClassName = e.ClassName, Origin = e.Origin, Angles = e.Angles,
        Properties = e.Properties
    }).ToList();

    var doc = MapEmitter.Emit(boxes, ents);
    PrintCensus(doc);

    var text = Kv2Writer.Write(doc);
    File.WriteAllText(args[2], text);
    Console.WriteLine($"wrote {text.Length} chars to {args[2]}");

    // Our own writer must be readable by our own reader before we hand it
    // to dmxconvert. Cheap, and isolates writer bugs from Valve's opinion.
    var back = Kv2Reader.Read(text);
    if (!back.Ok) return Fail($"REREAD FAILED: {back.Failure} at {back.Offset}");
    Console.WriteLine("reread ok");
    return 0;
}

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
var bad = 0;
foreach (var (k, v) in census0)
{
    census2.TryGetValue(k, out var got);
    if (got != v) { Console.Error.WriteLine($"MISMATCH {k}: {v} -> {got}"); bad++; }
}
foreach (var (k, v) in census2)
    if (!census0.ContainsKey(k)) { Console.Error.WriteLine($"ADDED {k}: {v}"); bad++; }

if (bad != 0) return Fail($"census differs across the writer in {bad} type(s)");
Console.WriteLine("census identical across read -> write -> read");
return 0;
