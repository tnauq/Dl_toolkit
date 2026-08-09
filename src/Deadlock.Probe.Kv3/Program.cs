using System.Reflection;
using System.Text;

namespace Deadlock.Probe.Kv3;

// PROBE ONLY. Revision 2 — 2026-08-09.
//
// Revision 1 answered the round-trip question (REFORMATTED but semantically
// lossless, see the artifact). It ALSO tried to dump the API surface, but the
// type filter only matched names containing "KV3", so KVObject, KVValue and
// KVType were never printed — and dl-patch was then written against guessed
// signatures and failed to compile three times.
//
// This revision dumps the MUTATION surface properly: every type reachable from
// the KV3 namespace, with full member signatures, plus a live inspection of a
// real parsed document. Read the artifact before writing any code against it.

internal static class Program
{
    private static int Main(string[] args)
    {
        if (args.Length < 1)
        {
            Console.Error.WriteLine("usage: dl-probe-kv3 <input.vdata> [outdir]");
            return 2;
        }

        var input = args[0];
        var outDir = args.Length > 1 ? args[1] : "probe-out";

        if (!File.Exists(input))
        {
            Console.Error.WriteLine($"input not found: {input}");
            return 4;
        }

        Directory.CreateDirectory(outDir);

        DumpNamespaceSurface(outDir);

        try
        {
            InspectLiveDocument(input, outDir);
        }
        catch (Exception e)
        {
            Console.Error.WriteLine($"[probe] live inspection failed: {e.GetType().Name}: {e.Message}");
            File.WriteAllText(Path.Combine(outDir, "live-inspect.txt"),
                $"FAILED: {e.GetType().Name}: {e.Message}\n{e.StackTrace}\n");
        }

        Console.Error.WriteLine("[probe] done — read kv3-surface.txt and live-inspect.txt");
        return 0;
    }

    /// <summary>
    /// Everything in the KeyValues namespace, members included. No name filter
    /// this time — the filter is what hid the answer last run.
    /// </summary>
    private static void DumpNamespaceSurface(string outDir)
    {
        var sb = new StringBuilder();
        var asm = typeof(ValveResourceFormat.Resource).Assembly;

        sb.AppendLine("# VRF KV3 mutation surface");
        sb.AppendLine($"assembly: {asm.FullName}");
        sb.AppendLine();

        var types = asm.GetExportedTypes()
            .Where(t => t.Namespace is not null &&
                        t.Namespace.Contains("KeyValues", StringComparison.Ordinal))
            .OrderBy(t => t.FullName, StringComparer.Ordinal)
            .ToList();

        sb.AppendLine($"{types.Count} exported types in *KeyValues* namespaces");
        sb.AppendLine();

        foreach (var t in types)
        {
            sb.AppendLine($"## {t.FullName}{(t.IsEnum ? "  [enum]" : "")}");

            if (t.IsEnum)
            {
                foreach (var name in Enum.GetNames(t))
                    sb.AppendLine($"  {name} = {Convert.ToInt64(Enum.Parse(t, name))}");
                sb.AppendLine();
                continue;
            }

            foreach (var c in t.GetConstructors())
                sb.AppendLine($"  ctor      {c}");

            foreach (var p in t.GetProperties(BindingFlags.Public | BindingFlags.Instance |
                                              BindingFlags.Static | BindingFlags.DeclaredOnly))
                sb.AppendLine($"  property  {p.PropertyType.Name} {p.Name} " +
                              $"{{ {(p.CanRead ? "get; " : "")}{(p.CanWrite ? "set; " : "")}}}");

            foreach (var m in t.GetMethods(BindingFlags.Public | BindingFlags.Instance |
                                           BindingFlags.Static | BindingFlags.DeclaredOnly)
                         .Where(m => !m.IsSpecialName)
                         .OrderBy(m => m.Name, StringComparer.Ordinal))
                sb.AppendLine($"  method    {m}");

            foreach (var f in t.GetFields(BindingFlags.Public | BindingFlags.Instance |
                                          BindingFlags.Static | BindingFlags.DeclaredOnly))
                sb.AppendLine($"  field     {f.FieldType.Name} {f.Name}");

            sb.AppendLine();
        }

        File.WriteAllText(Path.Combine(outDir, "kv3-surface.txt"), sb.ToString());
        Console.Error.WriteLine($"[probe] wrote kv3-surface.txt ({types.Count} types)");
    }

    /// <summary>
    /// What the object graph looks like in practice: runtime types of Root, of
    /// a property entry, and of a scalar leaf. Signatures alone do not say
    /// whether Properties is settable or what a scalar's Value boxes to.
    /// </summary>
    private static void InspectLiveDocument(string input, string outDir)
    {
        var sb = new StringBuilder();
        var file = ValveResourceFormat.Serialization.KeyValues.KeyValues3.ParseKVFile(input);

        sb.AppendLine("# Live document inspection");
        sb.AppendLine($"input: {input}");
        sb.AppendLine();
        sb.AppendLine($"KV3File type : {file?.GetType().FullName}");

        var root = file?.Root;
        sb.AppendLine($"Root type    : {root?.GetType().FullName}");
        sb.AppendLine();

        if (root is null)
        {
            File.WriteAllText(Path.Combine(outDir, "live-inspect.txt"), sb.ToString());
            return;
        }

        // How do we enumerate an object's children, and what do we get back?
        sb.AppendLine("## Root members (runtime)");
        foreach (var p in root.GetType().GetProperties())
            sb.AppendLine($"  property  {p.PropertyType.FullName} {p.Name} " +
                          $"{{ {(p.CanRead ? "get; " : "")}{(p.CanWrite ? "set; " : "")}}}");
        foreach (var m in root.GetType().GetMethods()
                     .Where(m => !m.IsSpecialName)
                     .OrderBy(m => m.Name, StringComparer.Ordinal))
            sb.AppendLine($"  method    {m}");
        sb.AppendLine();

        // Walk a few levels and report the runtime type of everything we meet.
        sb.AppendLine("## First few entries, with runtime types");
        var propsProp = root.GetType().GetProperty("Properties");
        sb.AppendLine($"Properties property: {propsProp?.PropertyType.FullName ?? "(none)"}");
        sb.AppendLine($"Properties settable: {propsProp?.CanWrite}");
        sb.AppendLine();

        if (propsProp?.GetValue(root) is System.Collections.IEnumerable entries)
        {
            var n = 0;
            foreach (var entry in entries)
            {
                if (n++ >= 12) break;
                var et = entry.GetType();
                var key = et.GetProperty("Key")?.GetValue(entry);
                var val = et.GetProperty("Value")?.GetValue(entry);
                sb.AppendLine($"  [{n}] entryType={et.FullName}");
                sb.AppendLine($"      key={key}");
                sb.AppendLine($"      valueType={val?.GetType().FullName}");

                if (val is not null)
                {
                    var vt = val.GetType();
                    foreach (var p in vt.GetProperties())
                    {
                        object? pv;
                        try { pv = p.GetValue(val); }
                        catch (Exception ex) { pv = $"<threw {ex.GetType().Name}>"; }
                        sb.AppendLine($"        .{p.Name} ({p.PropertyType.Name}, " +
                                      $"{(p.CanWrite ? "settable" : "readonly")}) = " +
                                      $"{Short(pv)}  [runtime {pv?.GetType().Name}]");
                    }
                }
                sb.AppendLine();
            }
        }
        else
        {
            sb.AppendLine("  Properties is not enumerable — record what it actually is above.");
        }

        File.WriteAllText(Path.Combine(outDir, "live-inspect.txt"), sb.ToString());
        Console.Error.WriteLine("[probe] wrote live-inspect.txt");
    }

    private static string Short(object? v)
    {
        var s = v?.ToString() ?? "null";
        s = s.Replace("\n", "\\n").Replace("\t", "\\t");
        return s.Length <= 100 ? s : s[..100] + "…";
    }
}
