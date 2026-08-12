using Deadlock.Contracts;

namespace Deadlock.Patch;

/// <summary>
/// dl-patch batch — one plan, many files, all or nothing.
///
///   dl-patch batch --plan &lt;plan.json&gt; --root &lt;dir&gt; --out-root &lt;dir&gt;
///                  --source-build &lt;sha&gt; [--dry-run] [--json] [--max-files N]
///
/// Design decisions this file implements, all settled 2026-08-12. Each is here
/// because the alternative was considered and rejected, so changing one means
/// reopening that decision rather than adjusting a detail.
///
///   Q1  guards mandatory in the plan; explicit null opts out
///   Q2  numbers compared after 6dp normalisation (see Guard)
///   Q3  every document held in memory; nothing is written until all succeed
///   Q4  --out-root required and separate; output is a patch OVERLAY, so only
///       files named in the plan are written
///   Q7  --source-build required, carried in the envelope's pinned_build
///   Q12 --dry-run does the whole evaluation and writes nothing
///   Q13 file count capped, so the in-memory model fails with an error
///   Q15 every failure is evaluated and reported, never first-stop
///   Q16 every planned file appears in the envelope, changed or not
/// </summary>
internal static class BatchCommand
{
    public const int DefaultMaxFiles = 32;

    public const string Usage = """
        dl-patch batch — apply a plan of scalar edits across many vdata files

        usage:
          dl-patch batch --plan <plan.json> --root <dir> --out-root <dir>
                         --source-build <sha> [--dry-run] [--json] [--max-files N]

        options:
          --plan <path>         plan file (required)
          --root <dir>          tree the plan's relative paths resolve against (required)
          --out-root <dir>      where patched files are written (required)
          --source-build <sha>  build the inputs came from; recorded on the artifact (required)
          --dry-run             evaluate everything, write nothing
          --json                envelope on stdout
          --max-files N         cap on files in one plan (default 32)
          -h, --help            this text

        plan shape:
          {
            "version": 1,
            "description": "optional human note",
            "edits": [
              { "file": "game/citadel/pak01_dir/scripts/heroes.vdata",
                "set": [
                  { "path": "hero_base.m_mapStartingStats.EMaxHealth",
                    "value": 750, "expect": 780 },
                  { "path": "hero_base.m_bDisabled",
                    "value": false, "expect": null }
                ] } ]
          }

        Every 'set' entry MUST carry 'expect'. Use null to opt out deliberately.
        Unknown fields and unsupported versions are refused, not ignored.
        One entry per file; one edit per path.

        Output is an OVERLAY: only files named in the plan are written to
        --out-root. Nothing under --root is modified.

        exit: 0 ok · 2 misuse · 4 input unreadable · 5 path not found
              6 type mismatch · 7 guard failed (the build moved)
        """;

    public static int Run(string[] args)
    {
        string? planPath = null, root = null, outRoot = null, sourceBuild = null;
        bool dryRun = false, json = false;
        var maxFiles = DefaultMaxFiles;

        for (var i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "-h":
                case "--help":
                    Console.Error.WriteLine(Usage);
                    return Exit.Ok;

                case "--plan":
                    if (++i >= args.Length) return Misuse("--plan needs a path", json);
                    planPath = args[i];
                    break;

                case "--root":
                    if (++i >= args.Length) return Misuse("--root needs a directory", json);
                    root = args[i];
                    break;

                case "--out-root":
                    if (++i >= args.Length) return Misuse("--out-root needs a directory", json);
                    outRoot = args[i];
                    break;

                case "--source-build":
                    if (++i >= args.Length) return Misuse("--source-build needs a value", json);
                    sourceBuild = args[i];
                    break;

                case "--max-files":
                    if (++i >= args.Length) return Misuse("--max-files needs a number", json);
                    if (!int.TryParse(args[i], out maxFiles) || maxFiles < 1)
                        return Misuse($"--max-files must be a positive integer, got: {args[i]}", json);
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

        if (planPath is null) return Misuse("--plan is required", json);
        if (root is null) return Misuse("--root is required", json);
        if (outRoot is null) return Misuse("--out-root is required", json);
        // D2: an artifact with no build id is an unlabelled artifact.
        if (sourceBuild is null) return Misuse("--source-build is required", json);

        if (!File.Exists(planPath))
            return Fail(null, sourceBuild, ErrorCode.InputNotFound,
                $"plan not found: {planPath}", "check the path", PatchExit.InputUnreadable, json);

        if (!Directory.Exists(root))
            return Fail(null, sourceBuild, ErrorCode.InputNotFound,
                $"--root does not exist: {root}", "clone the fixture tree first",
                PatchExit.InputUnreadable, json);

        string planText;
        try
        {
            planText = File.ReadAllText(planPath);
        }
        catch (Exception ex)
        {
            return Fail(null, sourceBuild, ErrorCode.InputUnreadable,
                $"could not read {planPath}: {ex.Message}", "check permissions",
                PatchExit.InputUnreadable, json);
        }

        if (!Plan.TryParse(planText, out var plan, out var planError))
            return Fail(null, sourceBuild, ErrorCode.PlanInvalid, planError!,
                "see --help for the accepted plan shape", Exit.Misuse, json);

        if (plan!.Files.Count > maxFiles)
            return Fail(null, sourceBuild, ErrorCode.TooManyFiles,
                $"plan touches {plan.Files.Count} files; the cap is {maxFiles}",
                "raise --max-files if this is deliberate; every file is held in memory",
                Exit.Misuse, json);

        // ---- load every document up front ---------------------------------
        var docs = new Dictionary<string, Kv3Document>(StringComparer.Ordinal);
        var reports = new Dictionary<string, BatchFileReport>(StringComparer.Ordinal);
        foreach (var pf in plan.Files)
            reports[pf.File] = new BatchFileReport { File = pf.File };

        foreach (var pf in plan.Files)
        {
            var full = System.IO.Path.Combine(root, pf.File);
            if (!File.Exists(full))
                return Fail(Data(plan, planPath, root, outRoot, dryRun, reports),
                    sourceBuild, ErrorCode.InputNotFound,
                    $"input not found: {full}",
                    "check the plan's paths are relative to --root",
                    PatchExit.InputUnreadable, json);

            try
            {
                docs[pf.File] = Kv3Document.Load(full);
            }
            catch (Exception ex)
            {
                return Fail(Data(plan, planPath, root, outRoot, dryRun, reports),
                    sourceBuild, ErrorCode.InputUnreadable,
                    $"could not parse {pf.File} as KV3: {ex.GetType().Name}: {ex.Message}",
                    "batch reads uncompiled source vdata; compiled .vdata_c is not supported",
                    PatchExit.InputUnreadable, json);
            }
        }

        // ---- phase 1: evaluate every guard, change nothing -----------------
        // Q15: all of them, so one dry run shows the full extent of the drift.
        var guardFailures = 0;
        var pathMisses = 0;
        foreach (var pf in plan.Files)
        {
            var doc = docs[pf.File];
            var report = reports[pf.File];

            foreach (var ps in pf.Sets)
            {
                var readOk = doc.TryRead(ps.Path, out var current, out var readError);

                if (!readOk)
                {
                    // Q9: a guarded path that has vanished is drift, not a typo.
                    var isMissing = readError is not null &&
                                    readError.Contains("path not found", StringComparison.Ordinal);
                    if (ps.Guarded && isMissing)
                    {
                        guardFailures++;
                        report.Failed++;
                        report.Edits.Add(new EditReport
                        {
                            Path = ps.Path,
                            From = null,
                            To = ps.Value.ToString(),
                            Expected = ps.Expect!.ToString(),
                            Ok = false,
                            Error = $"guard failed: path is gone from this build ({readError})"
                        });
                        continue;
                    }

                    if (isMissing) pathMisses++;
                    report.Failed++;
                    report.Edits.Add(new EditReport
                    {
                        Path = ps.Path,
                        From = null,
                        To = ps.Value.ToString(),
                        Expected = ps.Guarded ? ps.Expect!.ToString() : null,
                        Ok = false,
                        Error = readError
                    });
                    continue;
                }

                if (ps.Guarded && !Guard.Matches(current, ps.Expect!, out var actual))
                {
                    guardFailures++;
                    report.Failed++;
                    report.Edits.Add(new EditReport
                    {
                        Path = ps.Path,
                        From = actual,
                        To = ps.Value.ToString(),
                        Expected = ps.Expect!.ToString(),
                        Ok = false,
                        Error = $"guard failed: expected {ps.Expect}, found {actual}"
                    });
                    continue;
                }

                // Placeholder; phase 2 replaces it once the plan is known good.
                report.Edits.Add(new EditReport
                {
                    Path = ps.Path,
                    From = Kv3Document.Show(current),
                    To = ps.Value.ToString(),
                    Expected = ps.Guarded ? ps.Expect!.ToString() : null,
                    Noop = Guard.Matches(current, ps.Value, out _),
                    Ok = true
                });
            }
        }

        if (guardFailures > 0 || pathMisses > 0 || reports.Values.Any(r => r.Failed > 0))
        {
            Recount(reports);
            var data = Data(plan, planPath, root, outRoot, dryRun, reports);

            if (guardFailures > 0)
                return Fail(data, sourceBuild, ErrorCode.GuardFailed,
                    $"{guardFailures} guard(s) failed; nothing written",
                    "the build moved underneath this plan — re-derive it against the current source-build",
                    PatchExit.GuardFailed, json);

            return Fail(data, sourceBuild, ErrorCode.PathNotFound,
                $"{reports.Values.Sum(r => r.Failed)} edit(s) could not be resolved; nothing written",
                "check the dotted paths against the source vdata; every segment must exist",
                PatchExit.PathNotFound, json);
        }

        // ---- phase 2: apply in memory --------------------------------------
        foreach (var pf in plan.Files)
        {
            var doc = docs[pf.File];
            var report = reports[pf.File];
            report.Edits.Clear();

            foreach (var ps in pf.Sets)
            {
                doc.TryRead(ps.Path, out var before, out _);
                var noop = Guard.Matches(before, ps.Value, out _);

                var result = doc.Apply(new Edit(ps.Path, ps.Value));
                var er = EditReport.Of(result);
                er.Expected = ps.Guarded ? ps.Expect!.ToString() : null;
                er.Noop = noop && result.Ok;
                report.Edits.Add(er);

                if (!result.Ok) report.Failed++;
                else if (er.Noop) report.Skipped++;
                else report.Applied++;
            }
        }

        if (reports.Values.Any(r => r.Failed > 0))
        {
            var data = Data(plan, planPath, root, outRoot, dryRun, reports);
            return Fail(data, sourceBuild, ErrorCode.TypeMismatch,
                $"{reports.Values.Sum(r => r.Failed)} edit(s) failed; nothing written",
                "the document's existing type wins; a fractional value into an integer field is refused",
                PatchExit.TypeMismatch, json);
        }

        // ---- phase 3: write, only now that everything has succeeded --------
        if (!dryRun)
        {
            foreach (var pf in plan.Files)
            {
                var dest = System.IO.Path.Combine(outRoot, pf.File);
                try
                {
                    var dir = System.IO.Path.GetDirectoryName(dest);
                    if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
                    File.WriteAllText(dest, docs[pf.File].Serialize());
                    reports[pf.File].Written = true;
                }
                catch (Exception ex)
                {
                    // Files already written stay written. All-or-nothing is
                    // enforced by staging in memory, which removes every
                    // failure mode BEFORE this loop; a mid-loop I/O error is
                    // reported honestly rather than pretended away.
                    var data = Data(plan, planPath, root, outRoot, dryRun, reports);
                    return Fail(data, sourceBuild, ErrorCode.OutputUnwritable,
                        $"could not write {dest}: {ex.Message}",
                        "some files may already have been written; check --out-root",
                        PatchExit.InputUnreadable, json);
                }
            }
        }

        return Emit(Data(plan, planPath, root, outRoot, dryRun, reports),
                    sourceBuild, null, Exit.Ok, json);
    }

    private static void Recount(Dictionary<string, BatchFileReport> reports)
    {
        foreach (var r in reports.Values)
        {
            r.Applied = r.Edits.Count(e => e.Ok && !e.Noop);
            r.Skipped = r.Edits.Count(e => e.Ok && e.Noop);
            r.Failed = r.Edits.Count(e => !e.Ok);
        }
    }

    private static BatchData Data(Plan plan, string planPath, string root, string outRoot,
                                  bool dryRun, Dictionary<string, BatchFileReport> reports)
    {
        // Q6: apply in plan order, EMIT sorted, so two runs of one plan give
        // byte-identical envelopes however the plan was written.
        var files = reports.Values
            .OrderBy(f => f.File, StringComparer.Ordinal)
            .ToList();
        foreach (var f in files)
            f.Edits = f.Edits.OrderBy(e => e.Path, StringComparer.Ordinal).ToList();

        return new BatchData
        {
            DryRun = dryRun,
            PlanPath = planPath,
            Description = plan.Description,
            Root = root,
            OutRoot = dryRun ? null : outRoot,
            FilesTotal = files.Count,
            Applied = files.Sum(f => f.Applied),
            Skipped = files.Sum(f => f.Skipped),
            Failed = files.Sum(f => f.Failed),
            Files = files
        };
    }

    private static int Misuse(string message, bool json)
    {
        if (json)
        {
            Json.ToStdout(new Envelope<BatchData>
            {
                Tool = Tool.Name,
                Version = Tool.Version,
                Ok = false,
                Errors = { new ToolError(ErrorCode.Misuse, message, "see 'dl-patch batch --help'") }
            });
        }
        Console.Error.WriteLine($"error: {message}");
        Console.Error.WriteLine();
        Console.Error.WriteLine(Usage);
        return Exit.Misuse;
    }

    private static int Fail(BatchData? data, string sourceBuild, string code,
                            string message, string fix, int exitCode, bool json)
        => Emit(data ?? new BatchData(), sourceBuild, new ToolError(code, message, fix), exitCode, json);

    private static int Emit(BatchData data, string sourceBuild, ToolError? error, int code, bool json)
    {
        var envelope = new Envelope<BatchData>
        {
            Tool = Tool.Name,
            Version = Tool.Version,
            PinnedBuild = sourceBuild,
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
            foreach (var f in data.Files)
            {
                Console.Error.WriteLine($"  {f.File}");
                foreach (var e in f.Edits)
                {
                    Console.Error.WriteLine(e.Ok
                        ? (e.Noop
                            ? $"    noop  {e.Path}: already {e.To}"
                            : $"    ok    {e.Path}: {e.From} -> {e.To}")
                        : $"    FAIL  {e.Path}: {e.Error}");
                }
            }
            if (error is not null)
            {
                Console.Error.WriteLine($"error: {error.Message}");
                Console.Error.WriteLine($"  fix: {error.Fix}");
            }
            else if (data.DryRun)
            {
                Console.Error.WriteLine(
                    $"dry run: {data.Applied} edits would apply across {data.FilesTotal} files " +
                    $"({data.Skipped} already at target)");
            }
            else
            {
                Console.Error.WriteLine(
                    $"wrote {data.FilesTotal} files to {data.OutRoot} " +
                    $"({data.Applied} edits, {data.Skipped} no-ops, structurally valid)");
            }
        }

        return code;
    }
}
