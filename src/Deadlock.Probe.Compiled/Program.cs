// THROWAWAY PROBE — delete once the findings are in FINDINGS.md.
// Same status as src/Deadlock.Probe.Kv3 was.
//
// QUESTION (Q9, maps track): can VRF read a COMPILED Source 2 resource, and
// does the payload come back as a KV3 object we can walk?
//
// Everything in the toolkit so far reads UNCOMPILED source vdata via
// KeyValues3.ParseKVFile. A map ships only compiled resources — .vents_c,
// .vwrld_c, .vmap_c — with no source recoverable (FINDINGS-maps-2026-08-13 §3).
// So whether map READING tools can reuse the vdata layer depends entirely on
// this, and it has never been tested.
//
// METHOD. The VRF compiled-resource API has NOT been read, so this does not
// assume a shape. It tries several routes, each in its own try/catch, and
// reports what happened for every one. A route that throws prints its
// exception type and the probe continues — the point is to learn the surface,
// not to succeed.
//
// The input is a .vdata_c WE compiled ourselves in CI, so no third-party file
// is involved. That answers the general question (can VRF open a compiled
// resource); whether map-specific lumps behave the same is a follow-up.

using System.Reflection;

var path = args.Length > 0 ? args[0] : null;
var sourcePath = args.Length > 1 ? args[1] : null;
if (path is null || !File.Exists(path))
{
    Console.Error.WriteLine("usage: probe-compiled <file.vdata_c> [source.vdata]");
    return 2;
}

Console.WriteLine($"input: {path} ({new FileInfo(path).Length} bytes)");
Console.WriteLine();

// ---------------------------------------------------------------------------
// Route 0 — what does the resource assembly even expose?
// Printed first so that if every route below fails, the run still tells us the
// real type and member names to write against next time.
// ---------------------------------------------------------------------------
Console.WriteLine("=== route 0: surface of ValveResourceFormat ===");
try
{
    var asm = typeof(ValveResourceFormat.Resource).Assembly;
    Console.WriteLine($"assembly: {asm.GetName().Name} {asm.GetName().Version}");

    var res = typeof(ValveResourceFormat.Resource);
    Console.WriteLine($"type: {res.FullName}");
    foreach (var m in res.GetMethods(BindingFlags.Public | BindingFlags.Instance)
                         .Where(m => !m.IsSpecialName)
                         .OrderBy(m => m.Name).Take(30))
        Console.WriteLine($"  method  {m.Name}({string.Join(", ", m.GetParameters().Select(p => p.ParameterType.Name))})");
    foreach (var p in res.GetProperties(BindingFlags.Public | BindingFlags.Instance)
                         .OrderBy(p => p.Name))
        Console.WriteLine($"  prop    {p.PropertyType.Name} {p.Name}");
}
catch (Exception ex)
{
    Console.WriteLine($"  FAILED {ex.GetType().Name}: {ex.Message}");
}
Console.WriteLine();

// ---------------------------------------------------------------------------
// Route 1 — the source-vdata path, pointed at a compiled file.
// Expected to fail. Worth one line to confirm the failure is clean and named,
// because that is what a user will hit if they aim dl at a .vdata_c.
// ---------------------------------------------------------------------------
Console.WriteLine("=== route 1: KeyValues3.ParseKVFile (the source path) ===");
try
{
    var file = ValveResourceFormat.Serialization.KeyValues.KeyValues3.ParseKVFile(path);
    Console.WriteLine($"  UNEXPECTED SUCCESS — root null? {file?.Root is null}");
}
catch (Exception ex)
{
    Console.WriteLine($"  failed as expected: {ex.GetType().Name}: {ex.Message}");
}
Console.WriteLine();

// ---------------------------------------------------------------------------
// Route 2 — Resource.Read, the documented entry point for compiled files.
// ---------------------------------------------------------------------------
Console.WriteLine("=== route 2: Resource.Read ===");
try
{
    using var resource = new ValveResourceFormat.Resource();
    resource.Read(path);

    Console.WriteLine($"  ok. ResourceType = {resource.ResourceType}");

    try
    {
        Console.WriteLine($"  blocks: {resource.Blocks.Count}");
        foreach (var b in resource.Blocks)
            Console.WriteLine($"    {b.Type}  offset {b.Offset}  size {b.Size}");
    }
    catch (Exception ex)
    {
        Console.WriteLine($"  block listing failed: {ex.GetType().Name}: {ex.Message}");
    }

    // The payload. For a vdata this should be the KV3 document itself.
    try
    {
        var data = resource.DataBlock;
        Console.WriteLine($"  DataBlock type: {data?.GetType().FullName ?? "null"}");

        if (data is not null)
        {
            foreach (var p in data.GetType()
                         .GetProperties(BindingFlags.Public | BindingFlags.Instance)
                         .OrderBy(p => p.Name).Take(15))
                Console.WriteLine($"    prop  {p.PropertyType.Name} {p.Name}");
        }
    }
    catch (Exception ex)
    {
        Console.WriteLine($"  DataBlock failed: {ex.GetType().Name}: {ex.Message}");
    }
}
catch (Exception ex)
{
    Console.WriteLine($"  FAILED {ex.GetType().Name}: {ex.Message}");
}
Console.WriteLine();

// ---------------------------------------------------------------------------
// Route 3 — can the payload be walked as KV3, the way Kv3Document does?
// This is the actual question: if yes, map reading reuses the vdata layer.
// ---------------------------------------------------------------------------
Console.WriteLine("=== route 3: is the payload a walkable KVObject? ===");
try
{
    using var resource = new ValveResourceFormat.Resource();
    resource.Read(path);

    object? candidate = resource.DataBlock;
    var found = false;

    if (candidate is not null)
    {
        foreach (var p in candidate.GetType().GetProperties(BindingFlags.Public | BindingFlags.Instance))
        {
            object? v;
            try { v = p.GetValue(candidate); } catch { continue; }
            if (v is ValveResourceFormat.Serialization.KeyValues.KVObject kv)
            {
                found = true;
                Console.WriteLine($"  KVObject via .{p.Name}");
                Console.WriteLine($"    IsArray = {kv.IsArray}, properties = {kv.Properties.Count}");
                foreach (var key in kv.Properties.Keys.Take(12))
                    Console.WriteLine($"      key: {key}");
                break;
            }
        }
    }

    if (!found)
        Console.WriteLine("  no KVObject found on the data block — map reading needs its own path");
}
catch (Exception ex)
{
    Console.WriteLine($"  FAILED {ex.GetType().Name}: {ex.Message}");
}


// ---------------------------------------------------------------------------
// Route 4 — SOURCE vs COMPILED, the question that decides whether a
// cross-boundary diff is worth building.
//
// `loop` currently proves the compiled output of a patched file DIFFERS from
// the compiled output of the pristine one. That is much weaker than proving it
// differs CORRECTLY — nothing asserts the compiled resource actually holds the
// value we wrote rather than some other change.
//
// If flattening source and compiled yields the same path/value set, then
// `dl diff --old x.vdata --new x.vdata_c` reporting zero differences is a
// strong, falsifiable claim that compilation is value-preserving, and it is
// worth building. If it yields hundreds of spurious differences — compiler-
// added metadata, type normalisation — the feature is noise and needs a filter
// before it is worth anything.
//
// Counting is the whole point. Do not judge from the first few lines.
// ---------------------------------------------------------------------------
Console.WriteLine();
Console.WriteLine("=== route 4: source vs compiled, flattened ===");
if (sourcePath is null || !File.Exists(sourcePath))
{
    Console.WriteLine("  no source file given — skipped");
}
else
{
    try
    {
        var srcFile = ValveResourceFormat.Serialization.KeyValues.KeyValues3.ParseKVFile(sourcePath);
        var srcRoot = srcFile?.Root;

        using var resource = new ValveResourceFormat.Resource();
        resource.Read(path);
        var kv3 = resource.DataBlock as ValveResourceFormat.ResourceTypes.BinaryKV3;
        var cmpRoot = kv3?.Data;

        if (srcRoot is null || cmpRoot is null)
        {
            Console.WriteLine($"  could not obtain both roots (source null? {srcRoot is null}, compiled null? {cmpRoot is null})");
        }
        else
        {
            var a = new SortedDictionary<string, string>(StringComparer.Ordinal);
            var b = new SortedDictionary<string, string>(StringComparer.Ordinal);
            Flatten(srcRoot, "", a);
            Flatten(cmpRoot, "", b);

            Console.WriteLine($"  source paths:   {a.Count}");
            Console.WriteLine($"  compiled paths: {b.Count}");

            var onlySrc = a.Keys.Where(k => !b.ContainsKey(k)).ToList();
            var onlyCmp = b.Keys.Where(k => !a.ContainsKey(k)).ToList();
            var differing = a.Keys.Where(k => b.ContainsKey(k) && a[k] != b[k]).ToList();

            Console.WriteLine($"  only in source:   {onlySrc.Count}");
            Console.WriteLine($"  only in compiled: {onlyCmp.Count}");
            Console.WriteLine($"  present in both but differing: {differing.Count}");

            foreach (var k in onlySrc.Take(10)) Console.WriteLine($"    src-only  {k} = {a[k]}");
            foreach (var k in onlyCmp.Take(10)) Console.WriteLine($"    cmp-only  {k} = {b[k]}");
            foreach (var k in differing.Take(10)) Console.WriteLine($"    differs   {k}: {a[k]}  ->  {b[k]}");

            var total = onlySrc.Count + onlyCmp.Count + differing.Count;
            Console.WriteLine();
            Console.WriteLine(total == 0
                ? "  VERDICT: identical — a cross-boundary diff would be a strong assertion"
                : $"  VERDICT: {total} differences — a cross-boundary diff needs a filter to be useful");
        }
    }
    catch (Exception ex)
    {
        Console.WriteLine($"  FAILED {ex.GetType().Name}: {ex.Message}");
    }
}

Console.WriteLine();
Console.WriteLine("probe complete");
return 0;

// Local flatten, deliberately self-contained: a probe must not depend on the
// shipping code it exists to inform.
static void Flatten(ValveResourceFormat.Serialization.KeyValues.KVObject node,
                    string prefix, SortedDictionary<string, string> into)
{
    foreach (var kv in node.Properties)
    {
        var p = prefix.Length == 0 ? kv.Key : prefix + "." + kv.Key;
        var v = kv.Value;
        if (v.Value is ValveResourceFormat.Serialization.KeyValues.KVObject child)
        {
            if (child.IsArray)
            {
                into[p] = "[array:" + child.Properties.Count + "]";
                continue;
            }
            Flatten(child, p, into);
            continue;
        }
        into[p] = v.Value switch
        {
            null => "null",
            bool bo => bo ? "true" : "false",
            double d => d.ToString("F6", System.Globalization.CultureInfo.InvariantCulture),
            float f => ((double)f).ToString("F6", System.Globalization.CultureInfo.InvariantCulture),
            IFormattable i => i.ToString(null, System.Globalization.CultureInfo.InvariantCulture),
            _ => v.Value.ToString() ?? "null"
        };
    }
}
