namespace Deadlock.Patch;

/// <summary>
/// dl-patch v1 — hero vdata, scalars only.
///
///   dl-patch --in &lt;file&gt; --out &lt;file&gt; --set path=value [--set ...]
///            [--dry-run] [--json]
///
/// stdout is a machine interface (D5). Diagnostics go to stderr. Nothing but
/// the envelope is ever printed to stdout under --json.
///
/// It emits SOURCE vdata. Compiling is a separate step and a separate tool.
/// It says "structurally valid", never "works" — nothing here has been loaded
/// by the game (D7).
/// </summary>
internal static class Program
{
    private const string Usage = """
        dl-patch — set scalar values in a Deadlock source vdata file

        usage:
          dl-patch --in <file.vdata> --out <file.vdata> --set <path>=<value> [--set ...]
                   [--dry-run] [--json]

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

    private static int Main(string[] args)
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

        var env = new Envelope { DryRun = dryRun, Input = input, Output = dryRun ? null : output };

        if (!File.Exists(input))
        {
            env.Ok = false;
            env.Error = $"input not found: {input}";
            return Emit(env, Exit.InputUnreadable, json);
        }

        Kv3Document doc;
        try
        {
            doc = Kv3Document.Load(input);
        }
        catch (Exception ex)
        {
            env.Ok = false;
            env.Error = $"could not parse as KV3: {ex.GetType().Name}: {ex.Message}. " +
                        "v1 supports uncompiled source vdata; compiled .vdata_c is not supported.";
            return Emit(env, Exit.InputUnreadable, json);
        }

        var results = edits.Select(doc.Apply).ToList();
        env.Edits = results.Select(EditReport.From).ToList();
        env.Applied = results.Count(r => r.Ok);
        env.Failed = results.Count(r => !r.Ok);
        env.Ok = env.Failed == 0;

        // All-or-nothing. A half-applied stat change is worse than none, and
        // this is the behaviour batch will need — establish it here.
        if (env.Failed > 0)
        {
            env.Error = $"{env.Failed} of {results.Count} edits failed; nothing written";
            var code = results.Any(r => !r.Ok && r.Error is not null &&
                                        r.Error.Contains("path not found", StringComparison.Ordinal))
                ? Exit.PathNotFound
                : Exit.TypeMismatch;
            return Emit(env, code, json);
        }

        if (!dryRun)
        {
            try
            {
                doc.Save(output!);
            }
            catch (Exception ex)
            {
                env.Ok = false;
                env.Error = $"could not write {output}: {ex.Message}";
                return Emit(env, Exit.InputUnreadable, json);
            }
        }

        return Emit(env, Exit.Ok, json);
    }

    private static int Misuse(string message, bool json)
    {
        if (json)
        {
            var env = new Envelope { Ok = false, Error = message };
            Console.WriteLine(env.ToJson());
        }
        Console.Error.WriteLine($"error: {message}");
        Console.Error.WriteLine();
        Console.Error.WriteLine(Usage);
        return Exit.Misuse;
    }

    private static int Emit(Envelope env, int code, bool json)
    {
        if (json)
        {
            Console.WriteLine(env.ToJson());
        }
        else
        {
            foreach (var e in env.Edits)
            {
                Console.Error.WriteLine(e.Ok
                    ? $"  ok    {e.Path}: {e.From} -> {e.To}"
                    : $"  FAIL  {e.Path}: {e.Error}");
            }
            if (env.Error is not null) Console.Error.WriteLine($"error: {env.Error}");
            else if (env.DryRun) Console.Error.WriteLine($"dry run: {env.Applied} edits would apply");
            else Console.Error.WriteLine($"wrote {env.Output} ({env.Applied} edits, structurally valid)");
        }
        return code;
    }
}
