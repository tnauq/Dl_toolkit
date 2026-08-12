using Deadlock.Contracts;

namespace Deadlock.Patch;

/// <summary>
/// dl-patch diff — what changed between two source vdata files.
///
///   dl-patch diff --old &lt;file&gt; --new &lt;file&gt; [--json] [--max-entries N]
///                 [--paths-only]
///
/// WHY THIS EXISTS. Batch guards are mandatory (Q1) and a guard fails when the
/// build moved underneath the plan (Q8). `--dry-run` tells you a plan HAS gone
/// stale; diff tells you WHAT moved, which is what you need to re-derive it.
/// The two are complementary: dry-run answers "does my plan still apply", diff
/// answers "what do I have to change".
///
/// DESIGN, decided 2026-08-12:
///
///   - A SUBCOMMAND, not a new assembly. Kv3Document is designated the only
///     file that touches VRF; a second assembly would mean duplicating that
///     access or refactoring out a shared vdata layer, and D8 says one tool at
///     a time. Promoting to a standalone `dl-diff` is a rename once a second
///     consumer exists.
///   - SEMANTIC, not textual. It compares parsed values, so VRF's reformatting
///     (floats to 6dp, arrays exploded) produces ZERO differences. A textual
///     diff of a no-op round trip would report most of the file.
///   - Floats normalise to 6dp before comparison, for the same reason and
///     consistently with batch guards (Q2).
///   - Arrays are opaque: a length change registers, an element edit does not.
///     Their elements have no dotted path, so naming them would emit paths
///     dl-patch refuses. Stated, not hidden.
///
/// EXIT CODES. 0 means identical, 1 means differences found. Code 1 is
/// Contracts' ExpectedFailure and this is exactly what it is for: a completed
/// run whose assertion did not hold. Differences are a RESULT, not an error,
/// so `ok` stays true in the envelope and `errors` stays empty.
/// </summary>
internal static class DiffCommand
{
    public const int DefaultMaxEntries = 200;

    public const string Usage = """
        dl-patch diff — semantic difference between two source vdata files

        usage:
          dl-patch diff --old <file.vdata> --new <file.vdata>
                        [--json] [--max-entries N] [--paths-only]

        options:
          --old <path>      baseline file (required)
          --new <path>      file to compare against it (required)
          --json            envelope on stdout
          --max-entries N   cap entries in the report (default 200; counts are
                            always complete even when the list is truncated)
          --paths-only      omit values, list changed paths only
          -h, --help        this text

        semantics:
          Compares PARSED values, so reserialisation is invisible — diffing a
          file against its own no-op round trip reports nothing.
          Floats compare at 6 decimal places, matching batch guards.
          Arrays are opaque: a length change shows, an element edit does not.

        exit: 0 identical · 1 differences found · 2 misuse · 4 input unreadable
        """;

    public static int Run(string[] args)
    {
        string? oldPath = null, newPath = null;
        bool json = false, pathsOnly = false;
        var maxEntries = DefaultMaxEntries;

        for (var i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "-h":
                case "--help":
                    Console.Error.WriteLine(Usage);
                    return Exit.Ok;

                case "--old":
                    if (++i >= args.Length) return Misuse("--old needs a path", json);
                    oldPath = args[i];
                    break;

                case "--new":
                    if (++i >= args.Length) return Misuse("--new needs a path", json);
                    newPath = args[i];
                    break;

                case "--max-entries":
                    if (++i >= args.Length) return Misuse("--max-entries needs a number", json);
                    if (!int.TryParse(args[i], out maxEntries) || maxEntries < 1)
                        return Misuse($"--max-entries must be a positive integer, got: {args[i]}", json);
                    break;

                case "--paths-only":
                    pathsOnly = true;
                    break;

                case "--json":
                    json = true;
                    break;

                default:
                    return Misuse($"unknown argument: {args[i]}", json);
            }
        }

        if (oldPath is null) return Misuse("--old is required", json);
        if (newPath is null) return Misuse("--new is required", json);

        if (!TryLoad(oldPath, json, out var oldDoc, out var rc)) return rc;
        if (!TryLoad(newPath, json, out var newDoc, out rc)) return rc;

        var before = Index(oldDoc!);
        var after = Index(newDoc!);

        var entries = new List<DiffEntry>();

        foreach (var (path, cur) in after)
        {
            if (!before.TryGetValue(path, out var prev))
            {
                entries.Add(new DiffEntry
                {
                    Path = path,
                    Change = "added",
                    To = pathsOnly ? null : cur.Value,
                    Kind = cur.Kind
                });
                continue;
            }

            var kindChanged = !string.Equals(prev.Kind, cur.Kind, StringComparison.Ordinal);
            var valueChanged = !string.Equals(
                Kv3Document.Comparable(prev.Kind, prev.Value),
                Kv3Document.Comparable(cur.Kind, cur.Value),
                StringComparison.Ordinal);

            if (kindChanged || valueChanged)
            {
                entries.Add(new DiffEntry
                {
                    Path = path,
                    Change = kindChanged ? "retyped" : "changed",
                    From = pathsOnly ? null : prev.Value,
                    To = pathsOnly ? null : cur.Value,
                    Kind = kindChanged ? $"{prev.Kind} -> {cur.Kind}" : cur.Kind
                });
            }
        }

        foreach (var (path, prev) in before)
        {
            if (!after.ContainsKey(path))
            {
                entries.Add(new DiffEntry
                {
                    Path = path,
                    Change = "removed",
                    From = pathsOnly ? null : prev.Value,
                    Kind = prev.Kind
                });
            }
        }

        // Deterministic ordering is a contract (D5).
        entries.Sort((a, b) => string.CompareOrdinal(a.Path, b.Path));

        var data = new DiffData
        {
            Old = oldPath,
            New = newPath,
            OldPaths = before.Count,
            NewPaths = after.Count,
            Added = entries.Count(e => e.Change == "added"),
            Removed = entries.Count(e => e.Change == "removed"),
            Changed = entries.Count(e => e.Change == "changed"),
            Retyped = entries.Count(e => e.Change == "retyped"),
            Total = entries.Count,
            Truncated = entries.Count > maxEntries,
            Entries = entries.Take(maxEntries).ToList()
        };

        var envelope = new Envelope<DiffData>
        {
            Tool = Tool.Name,
            Version = Tool.Version,
            // Differences are a RESULT, not a failure. ok stays true.
            Ok = true,
            Data = data
        };

        if (json)
        {
            Json.ToStdout(envelope);
        }
        else
        {
            foreach (var e in data.Entries)
            {
                Console.Error.WriteLine(e.Change switch
                {
                    "added" => $"  +   {e.Path} = {e.To}",
                    "removed" => $"  -   {e.Path} (was {e.From})",
                    "retyped" => $"  !   {e.Path}: {e.Kind}",
                    _ => $"  ~   {e.Path}: {e.From} -> {e.To}"
                });
            }
            if (data.Truncated)
                Console.Error.WriteLine($"  ... {data.Total - data.Entries.Count} more");
            Console.Error.WriteLine(
                $"{data.Total} differences ({data.Added} added, {data.Removed} removed, " +
                $"{data.Changed} changed, {data.Retyped} retyped) across " +
                $"{data.OldPaths} -> {data.NewPaths} paths");
        }

        return data.Total == 0 ? Exit.Ok : Exit.ExpectedFailure;
    }

    private static Dictionary<string, (string Kind, string Value)> Index(Kv3Document doc)
    {
        var map = new Dictionary<string, (string, string)>(StringComparer.Ordinal);
        foreach (var (path, kind, value) in doc.Flatten())
            map[path] = (kind, value);   // last wins; KV3 keys are unique per block
        return map;
    }

    private static bool TryLoad(string path, bool json, out Kv3Document? doc, out int rc)
    {
        doc = null;
        rc = Exit.Ok;

        if (!File.Exists(path))
        {
            rc = Fail(ErrorCode.InputNotFound, $"input not found: {path}",
                      "check the path", PatchExit.InputUnreadable, json);
            return false;
        }

        try
        {
            doc = Kv3Document.Load(path);
            return true;
        }
        catch (Exception ex)
        {
            rc = Fail(ErrorCode.InputUnreadable,
                      $"could not parse {path} as KV3: {ex.GetType().Name}: {ex.Message}",
                      "diff reads uncompiled source vdata; compiled .vdata_c is not supported",
                      PatchExit.InputUnreadable, json);
            return false;
        }
    }

    private static int Fail(string code, string message, string fix, int exitCode, bool json)
    {
        if (json)
        {
            Json.ToStdout(new Envelope<DiffData>
            {
                Tool = Tool.Name,
                Version = Tool.Version,
                Ok = false,
                Errors = { new ToolError(code, message, fix) }
            });
        }
        Console.Error.WriteLine($"error: {message}");
        Console.Error.WriteLine($"  fix: {fix}");
        return exitCode;
    }

    private static int Misuse(string message, bool json)
    {
        if (json)
        {
            Json.ToStdout(new Envelope<DiffData>
            {
                Tool = Tool.Name,
                Version = Tool.Version,
                Ok = false,
                Errors = { new ToolError(ErrorCode.Misuse, message, "see 'dl-patch diff --help'") }
            });
        }
        Console.Error.WriteLine($"error: {message}");
        Console.Error.WriteLine();
        Console.Error.WriteLine(Usage);
        return Exit.Misuse;
    }
}
