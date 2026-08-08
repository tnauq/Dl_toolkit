using Deadlock.Contracts;
using Deadlock.Format;

// dl-mkfixture — write a synthetic VPK from known content and report what went
// in, with checksums computed independently of ValvePak.
//
// Exists so the Format layer can be exercised with NO game files. The manifest
// is the expected side of the round-trip: dl-extract reads the same archive
// back and the two must agree.

var argv = Environment.GetCommandLineArgs().Skip(1).ToArray();

if (argv.Contains("--help"))
{
    Console.Error.WriteLine("""
        dl-mkfixture — generate a synthetic VPK

          dl-mkfixture [output_dir.vpk]

        Default output: build/synthetic_dir.vpk
        Exit: 0 ok · 1 write failed
        """);
    return Exit.Misuse;
}

var output = argv.FirstOrDefault(a => !a.StartsWith("--")) ?? "build/synthetic_dir.vpk";

try
{
    var result = VpkWriter.CreateSynthetic(output);

    Json.ToStdout(new Envelope<ManifestResult>
    {
        Tool = "dl-mkfixture",
        Ok = true,
        PinnedBuild = Environment.GetEnvironmentVariable("DL_PINNED_BUILD"),
        Data = result,
    });

    Console.Error.WriteLine($"[dl-mkfixture] wrote {result.Entries.Count} entries -> {output}");
    return Exit.Ok;
}
catch (Exception ex)
{
    Json.ToStdout(new Envelope<ManifestResult>
    {
        Tool = "dl-mkfixture",
        Ok = false,
        Errors = { new ToolError(
            "WRITE_FAILED",
            ex.Message,
            "ValvePak's write API may differ from what this assumes — check AddFile/Write signatures.") }
    });
    return Exit.ExpectedFailure;
}
