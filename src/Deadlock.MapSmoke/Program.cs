using Deadlock.Format.Dmx;

// Usage:
//   Deadlock.MapSmoke info      <in.vmap.txt>
//   Deadlock.MapSmoke roundtrip <in.vmap.txt> <out.vmap.txt>
//
// `info` prints a census. `roundtrip` reads, rewrites, re-reads its own
// output and asserts the two censuses match, which catches a writer that
// drops elements without needing dmxconvert. The CI workflow then sends the
// rewritten text through dmxconvert to binary and back, which is the check
// that actually has an independent judge in it.

static int Fail(string msg) { Console.Error.WriteLine(msg); return 1; }

if (args.Length < 2) return Fail("usage: info <file> | roundtrip <in> <out>");

var mode = args[0];
var inPath = args[1];

if (!File.Exists(inPath)) return Fail($"no such file: {inPath}");

var text = File.ReadAllText(inPath);
Console.WriteLine($"read {text.Length} chars from {inPath}");

var r = Kv2Reader.Read(text);
if (!r.Ok) return Fail($"parse failed: {r.Failure} at offset {r.Offset}");

var doc = r.Document!;
Console.WriteLine($"encoding={doc.Encoding} {doc.EncodingVersion} " +
                  $"format={doc.Format} {doc.FormatVersion} roots={doc.Roots.Count}");

static SortedDictionary<string, int> Census(DmxDocument d)
{
    var c = new SortedDictionary<string, int>(StringComparer.Ordinal);
    foreach (var e in d.AllElements())
        c[e.TypeName] = c.TryGetValue(e.TypeName, out var n) ? n + 1 : 1;
    return c;
}

var census = Census(doc);
var total = 0;
foreach (var (k, v) in census) { total += v; }
Console.WriteLine($"elements={total}");
foreach (var (k, v) in census) Console.WriteLine($"  {v,6}  {k}");

if (mode == "info") return 0;

if (mode != "roundtrip") return Fail($"unknown mode: {mode}");
if (args.Length < 3) return Fail("roundtrip needs an output path");

var outPath = args[2];
var written = Kv2Writer.Write(doc);
File.WriteAllText(outPath, written);
Console.WriteLine($"wrote {written.Length} chars to {outPath}");

var r2 = Kv2Reader.Read(written);
if (!r2.Ok) return Fail($"REREAD FAILED: {r2.Failure} at offset {r2.Offset}");

var census2 = Census(r2.Document!);
var bad = 0;
foreach (var (k, v) in census)
{
    census2.TryGetValue(k, out var got);
    if (got != v) { Console.Error.WriteLine($"MISMATCH {k}: {v} -> {got}"); bad++; }
}
foreach (var (k, v) in census2)
{
    if (!census.ContainsKey(k)) { Console.Error.WriteLine($"ADDED {k}: {v}"); bad++; }
}

if (bad != 0) return Fail($"census differs across the writer in {bad} type(s)");

Console.WriteLine("census identical across read -> write -> read");
return 0;
