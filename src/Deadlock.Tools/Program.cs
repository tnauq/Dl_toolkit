using Deadlock.Contracts;
using Deadlock.Format;

// dl-extract — VPK/resource -> JSON.
// Currently implements --index only: read the directory, emit entry metadata.
// Body extraction lands once there is a fixture to test it against.

var args_ = Environment.GetCommandLineArgs().Skip(1).ToArray();

if (args_.Length == 0 || args_.Contains("--help"))
{
    Console.Error.WriteLine("""
        dl-extract — read a VPK directory

          dl-extract <path-to-dir.vpk> [--index] [--summary] [--json]

          --index     emit per-entry metadata (default)
          --summary   counts and types only, no entry list
          --json      emit the standard envelope (currently always on)

        Exit: 0 ok · 2 misuse · 3 missing file
        """);
    return Exit.Misuse;
}

var path = args_.FirstOrDefault(a => !a.StartsWith("--"));
var summaryOnly = args_.Contains("--summary");

if (path is null)
{
    Json.ToStdout(new Envelope<VpkIndexResult>
    {
        Tool = "dl-extract",
        Ok = false,
        Errors = { new ToolError(
            "NO_INPUT",
            "No VPK path given.",
            "Pass the path to a *_dir.vpk file as the first argument.") }
    });
    return Exit.Misuse;
}

if (!File.Exists(path))
{
    Json.ToStdout(new Envelope<VpkIndexResult>
    {
        Tool = "dl-extract",
        Ok = false,
        Errors = { new ToolError(
            "FIXTURE_MISSING",
            $"No such file: {path}",
            "Commit a VPK to fixtures/, or pass a path to one. See AGENTS.md.") }
    });
    return Exit.MissingDependency;
}

try
{
    var result = VpkIndex.Read(path, includeEntries: !summaryOnly);

    var envelope = new Envelope<VpkIndexResult>
    {
        Tool = "dl-extract",
        Ok = true,
        PinnedBuild = Environment.GetEnvironmentVariable("DL_PINNED_BUILD"),
        Data = result,
    };

    if (envelope.PinnedBuild is null)
        envelope.Warnings.Add(
            "DL_PINNED_BUILD unset — output cannot be attributed to a build.");

    Json.ToStdout(envelope);
    Console.Error.WriteLine($"[dl-extract] {result.EntryCount} entries, {result.Types.Count} types");
    return Exit.Ok;
}
catch (Exception ex)
{
    Json.ToStdout(new Envelope<VpkIndexResult>
    {
        Tool = "dl-extract",
        Ok = false,
        Errors = { new ToolError(
            "READ_FAILED",
            ex.Message,
            "Confirm this is a *_dir.vpk and not a numbered data file such as pak01_001.vpk.") }
    });
    return Exit.ExpectedFailure;
}
