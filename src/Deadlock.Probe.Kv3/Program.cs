using System.Reflection;
using System.Text;

namespace Deadlock.Probe.Kv3;

// PROBE ONLY.
//
// Question: does ValveResourceFormat already give us a usable KV3 TEXT
// serializer, or do we have to write one for dl-patch?
//
// Method: take a real hero vdata (source text KV3) from GameTracking-Deadlock,
// parse it with VRF, serialize it straight back with NO edit, and diff.
//
// Three possible answers, and the probe must distinguish them:
//   IDENTICAL   byte-for-byte equal        -> wrap VRF, dl-patch is small
//   REFORMATTED parses back to same shape,
//               bytes differ               -> usable, but no byte assertion
//   LOSSY       content actually missing   -> write our own serializer
//
// Exit codes follow the project convention:
//   0 probe ran and reported          2 misuse (bad args)
//   3 missing dependency / API absent 4 probe ran, input unreadable
//
// Note: exit 0 means THE PROBE SUCCEEDED, not that the round trip was clean.
// The classification is in the report, not the exit code. Do not wire CI to
// fail on a REFORMATTED result — that is a legitimate finding.

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

        var originalBytes = File.ReadAllBytes(input);
        var originalText = File.ReadAllText(input);

        Console.Error.WriteLine($"[probe] input       {input}");
        Console.Error.WriteLine($"[probe] size        {originalBytes.Length} bytes");
        Console.Error.WriteLine($"[probe] first line  {FirstLine(originalText)}");

        // ---- 1. what does VRF actually expose? -----------------------------
        // Written before the API was read (see FINDINGS corrections, entry 1).
        // So: dump the surface first, then try to use it. If the call below is
        // wrong, the dump is what tells the next session the right name.
        DumpKv3Surface(outDir);

        string? roundTripped;
        try
        {
            roundTripped = RoundTrip(input);
        }
        catch (TypeLoadException e)
        {
            Console.Error.WriteLine($"[probe] VRF KV3 type not found: {e.Message}");
            Console.Error.WriteLine("[probe] see kv3-surface.txt for what IS exposed");
            return 3;
        }
        catch (MissingMethodException e)
        {
            Console.Error.WriteLine($"[probe] VRF KV3 method not found: {e.Message}");
            Console.Error.WriteLine("[probe] see kv3-surface.txt for what IS exposed");
            return 3;
        }
        catch (Exception e)
        {
            // A parse failure IS an answer: it means VRF cannot read source
            // vdata, which is itself decisive for dl-patch.
            Console.Error.WriteLine($"[probe] round trip threw: {e.GetType().Name}: {e.Message}");
            File.WriteAllText(Path.Combine(outDir, "report.md"),
                Report("THREW", originalBytes.Length, 0, $"{e.GetType().Name}: {e.Message}", null));
            return 0;
        }

        if (roundTripped is null)
        {
            Console.Error.WriteLine("[probe] serializer returned null");
            File.WriteAllText(Path.Combine(outDir, "report.md"),
                Report("NULL", originalBytes.Length, 0, "serializer returned null", null));
            return 0;
        }

        // ---- 2. classify ---------------------------------------------------
        var outPath = Path.Combine(outDir, "roundtrip.vdata");
        File.WriteAllText(outPath, roundTripped);
        var newBytes = File.ReadAllBytes(outPath);

        var identical = originalBytes.AsSpan().SequenceEqual(newBytes);
        var divergence = identical ? null : FirstDivergence(originalText, roundTripped);

        var verdict = identical
            ? "IDENTICAL"
            : LooksLossy(originalText, roundTripped) ? "LOSSY-SUSPECT" : "REFORMATTED";

        Console.Error.WriteLine($"[probe] verdict     {verdict}");
        Console.Error.WriteLine($"[probe] out size    {newBytes.Length} bytes");
        if (divergence is not null)
            Console.Error.WriteLine($"[probe] first diff  {divergence.Replace("\n", " | ")}");

        File.WriteAllText(Path.Combine(outDir, "report.md"),
            Report(verdict, originalBytes.Length, newBytes.Length, null, divergence));

        return 0;
    }

    // Adjust here if the surface dump says the names differ.
    private static string? RoundTrip(string path)
    {
        var kv = ValveResourceFormat.Serialization.KeyValues.KeyValues3.ParseKVFile(path);
        return kv?.ToString();
    }

    private static void DumpKv3Surface(string outDir)
    {
        var sb = new StringBuilder();
        sb.AppendLine("# VRF KV3 surface, as actually loaded");
        sb.AppendLine();

        var asm = typeof(ValveResourceFormat.Resource).Assembly;
        sb.AppendLine($"assembly: {asm.FullName}");
        sb.AppendLine();

        foreach (var t in asm.GetExportedTypes()
                     .Where(t => t.FullName is not null &&
                                 (t.FullName.Contains("KeyValues3", StringComparison.Ordinal) ||
                                  t.FullName.Contains("KV3", StringComparison.Ordinal)))
                     .OrderBy(t => t.FullName, StringComparer.Ordinal))
        {
            sb.AppendLine($"## {t.FullName}");
            foreach (var m in t.GetMembers(BindingFlags.Public | BindingFlags.Static |
                                           BindingFlags.Instance | BindingFlags.DeclaredOnly)
                         .OrderBy(m => m.Name, StringComparer.Ordinal))
            {
                sb.AppendLine($"  {m.MemberType,-10} {m}");
            }
            sb.AppendLine();
        }

        File.WriteAllText(Path.Combine(outDir, "kv3-surface.txt"), sb.ToString());
        Console.Error.WriteLine("[probe] wrote kv3-surface.txt");
    }

    // Cheap heuristic, NOT proof. Real loss needs eyes on the diff.
    private static bool LooksLossy(string a, string b)
    {
        var keysA = CountOccurrences(a, '=');
        var keysB = CountOccurrences(b, '=');
        return keysB < keysA * 0.98;
    }

    private static int CountOccurrences(string s, char c)
    {
        var n = 0;
        foreach (var ch in s) if (ch == c) n++;
        return n;
    }

    private static string FirstDivergence(string a, string b)
    {
        var la = a.ReplaceLineEndings("\n").Split('\n');
        var lb = b.ReplaceLineEndings("\n").Split('\n');
        var max = Math.Min(la.Length, lb.Length);
        for (var i = 0; i < max; i++)
        {
            if (!string.Equals(la[i], lb[i], StringComparison.Ordinal))
                return $"line {i + 1}\n  orig: {Trunc(la[i])}\n  new:  {Trunc(lb[i])}";
        }
        return $"identical for {max} lines, then length differs ({la.Length} vs {lb.Length})";
    }

    private static string Trunc(string s) =>
        s.Length <= 160 ? s : s[..160] + "…";

    private static string FirstLine(string s)
    {
        var i = s.IndexOf('\n');
        return Trunc(i < 0 ? s : s[..i]).Trim();
    }

    private static string Report(string verdict, int origSize, int newSize,
                                 string? error, string? divergence)
    {
        var sb = new StringBuilder();
        sb.AppendLine("# KV3 round-trip probe");
        sb.AppendLine();
        sb.AppendLine($"- verdict: **{verdict}**");
        sb.AppendLine($"- original: {origSize} bytes");
        sb.AppendLine($"- round-tripped: {newSize} bytes");
        if (error is not null) sb.AppendLine($"- error: `{error}`");
        sb.AppendLine();
        if (divergence is not null)
        {
            sb.AppendLine("## First divergence");
            sb.AppendLine();
            sb.AppendLine("```");
            sb.AppendLine(divergence);
            sb.AppendLine("```");
            sb.AppendLine();
        }
        sb.AppendLine("## What each verdict means for dl-patch");
        sb.AppendLine();
        sb.AppendLine("- `IDENTICAL` — wrap VRF. Byte-level assertions stay available.");
        sb.AppendLine("- `REFORMATTED` — VRF is usable, but the unchanged-bytes assertion");
        sb.AppendLine("  is off the table; CI has to compare parsed shape instead.");
        sb.AppendLine("- `LOSSY-SUSPECT` / `THREW` / `NULL` — we write the serializer.");
        sb.AppendLine();
        sb.AppendLine("Heuristics here are `[?]`. Read the artifact diff before recording");
        sb.AppendLine("anything as `[V-CI]` in FINDINGS.");
        return sb.ToString();
    }
}
