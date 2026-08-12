using Deadlock.Contracts;

namespace Deadlock.Patch;

/// <summary>Tool identity, shared by both front ends.</summary>
internal static class Tool
{
    public const string Name = "dl-patch";
    public const string Version = "0.2.0";
}

/// <summary>
/// dl-patch v1 — hero vdata, scalars only. The default mode.
///
///   dl-patch --in &lt;file&gt; --out &lt;file&gt; --set path=value [--set ...]
///            [--dry-run] [--json]
///
/// EXTRACTED from Program.cs 2026-08-12 when batch arrived. Behaviour is
/// unchanged — patch-smoke asserts on the exit codes and the error strings, so
/// this move is a move and nothing else.
///
/// stdout is a machine interface (D5). Diagnostics go to stderr. Nothing but
/// the envelope is ever printed to stdout under --json.
///
/// It emits SOURCE vdata. Compiling is a separate step and a separate tool.
/// It says "structurally valid", never "works" — nothing here has been loaded
/// by the game (D7).
/// </summary>
internal static class SetCommand
{
    public const string Usage = """
        dl-patch — set scalar values in a Deadlock source vdata file

        usage:
          dl-patch --in <file.vdata> --out <file.vdata> --set <path>=<value> [--set ...]
                   [--dry-run] [--json]
          dl-patch batch --plan <plan.json> ...        (see 'dl-patch batch --help')

        options:
          --in <path>       source vdata to read (required)
          --out <path>      where to write (required unless --dry-run)
          --set p=v         dotted path and new value; may repeat
          --dry-run         report what would change, write nothing
          --json            envelope on stdout
          -h, --help        this text

        scope:
          v1 sets SCALARS ONLY — numbers, strings, bools.
          Array indices, object insertion and typed values such as
          resource_name: are NOT supported and produce a named error.

        values:
          true / false            -> bool
          -12                     -> integer
          3.5                     -> number
          "1"                     -> string (quotes force string)
          anything else           -> string

        The existing type in the document wins. A fractional value written to
        an integer field is refused, not rounded.

        exit: 0 ok · 2 misuse · 3 missing dependency · 4 input unreadable
              5 path not found · 6 type mismatch
        """;

    public static int Run(string[] args)
    {
        string? input = null, output = null;
        var setArgs = new List<string>();
        bool dryRun = false, json = false;

        for (var i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "-h":
                case "--help":
                    Console.Error.WriteLine(Usage);
                    return Exit.Ok;

                case "--in":
                    if (++i >= args.Length) return Misuse("--in needs a path", json);
                    input = args[i];
                    break;

                case "--out":
                    if (++i >= args.Length) return Misuse("--out needs a path", json);
                    output = args[i];
                    break;

                case "--set":
                    if (++i >= args.Length) return Misuse("--set needs path=value", json);
                    setArgs.Add(args[i]);
                    break;

                case "--dry-run":
                    dryRun = true;
                    break;

                case "--json":
                    json = true;
                    break;

                default:
                    return Misuse($"unknown argument: {args[i]}", json);
            }
        }

        if (input is null) return Misuse("--in is required", json);
        if (output is null && !dryRun) return Misuse("--out is required unless --dry-run", json);
        if (setArgs.Count == 0) return Misuse("at least one --set is required", json);

        // Parse every --set before touching the file: argv errors should not
        // leave a half-written output.
        var edits = new List<Edit>();
        foreach (var s in setArgs)
        {
            if (!Edit.TryParse(s, out var e, out var err))
                return Misuse(err!, json);
            edits.Add(e!);
        }

        var effectiveOutput = dryRun ? null : output;

        if (!File.Exists(input))
        {
            return Emit(
                Data(dryRun, input, effectiveOutput, new List<EditReport>(), 0, 0),
                new ToolError(
                    ErrorCode.InputNotFound,
                    $"input not found: {input}",
                    "check the path, or clone the fixture from GameTracking-Deadlock"),
                PatchExit.InputUnreadable, json);
        }

        Kv3Document doc;
        try
        {
            doc = Kv3Document.Load(input);
        }
        catch (Exception ex)
        {
            return Emit(
                Data(dryRun, input, effectiveOutput, new List<EditReport>(), 0, 0),
                new ToolError(
                    ErrorCode.InputUnreadable,
                    $"could not parse as KV3: {ex.GetType().Name}: {ex.Message}",
                    "v1 supports uncompiled source vdata; compiled .vdata_c is not supported"),
                PatchExit.InputUnreadable, json);
        }

        var results = edits.Select(doc.Apply).ToList();
        var reports = results.Select(EditReport.Of).ToList();
        var applied = results.Count(r => r.Ok);
        var failed = results.Count(r => !r.Ok);

        // All-or-nothing. A half-applied stat change is worse than none, and
        // this is the behaviour batch needed — established here first.
        if (failed > 0)
        {
            var pathMiss = results.Any(r => !r.Ok && r.Error is not null &&
                                            r.Error.Contains("path not found", StringComparison.Ordinal));
            return Emit(
                Data(dryRun, input, effectiveOutput, reports, applied, failed),
                new ToolError(
                    pathMiss ? ErrorCode.PathNotFound : ErrorCode.TypeMismatch,
                    $"{failed} of {results.Count} edits failed; nothing written",
                    pathMiss
                        ? "check the dotted path against the source vdata; every segment must exist"
                        : "the document's existing type wins; quote a value to force a string"),
                pathMiss ? PatchExit.PathNotFound : PatchExit.TypeMismatch, json);
        }

        if (!dryRun)
        {
            try
            {
                doc.Save(output!);
            }
            catch (Exception ex)
            {
                return Emit(
                    Data(dryRun, input, effectiveOutput, reports, applied, failed),
                    new ToolError(
                        ErrorCode.OutputUnwritable,
                        $"could not write {output}: {ex.Message}",
                        "check the directory is writable and the path is not a directory"),
                    PatchExit.InputUnreadable, json);
            }
        }

        return Emit(
            Data(dryRun, input, effectiveOutput, reports, applied, failed),
            null, Exit.Ok, json);
    }

    private static PatchData Data(bool dryRun, string? input, string? output,
                                  List<EditReport> edits, int applied, int failed)
        => new()
        {
            DryRun = dryRun,
            Input = input,
            Output = output,
            Applied = applied,
            Failed = failed,
            Edits = edits
        };

    private static int Misuse(string message, bool json)
    {
        if (json)
        {
            Json.ToStdout(new Envelope<PatchData>
            {
                Tool = Tool.Name,
                Version = Tool.Version,
                Ok = false,
                Errors = { new ToolError(ErrorCode.Misuse, message, "see --help for the argument list") }
            });
        }
        Console.Error.WriteLine($"error: {message}");
        Console.Error.WriteLine();
        Console.Error.WriteLine(Usage);
        return Exit.Misuse;
    }

    private static int Emit(PatchData data, ToolError? error, int code, bool json)
    {
        var envelope = new Envelope<PatchData>
        {
            Tool = Tool.Name,
            Version = Tool.Version,
            Ok = error is null,
            Data = data
        };
        if (error is not null) envelope.Errors.Add(error);

        if (json)
        {
            Json.ToStdout(envelope);
        }
        else
        {
            foreach (var e in data.Edits)
            {
                Console.Error.WriteLine(e.Ok
                    ? $"  ok    {e.Path}: {e.From} -> {e.To}"
                    : $"  FAIL  {e.Path}: {e.Error}");
            }
            if (error is not null)
            {
                Console.Error.WriteLine($"error: {error.Message}");
                Console.Error.WriteLine($"  fix: {error.Fix}");
            }
            else if (data.DryRun)
            {
                Console.Error.WriteLine($"dry run: {data.Applied} edits would apply");
            }
            else
            {
                Console.Error.WriteLine(
                    $"wrote {data.Output} ({data.Applied} edits, structurally valid)");
            }
        }

        return code;
    }
}
