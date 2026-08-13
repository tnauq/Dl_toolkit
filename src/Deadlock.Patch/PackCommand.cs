using Deadlock.Contracts;
using Deadlock.Format;

namespace Deadlock.Patch;

/// <summary>
/// dl-patch pack — turn a compiled tree into an addon VPK.
///
///   dl-patch pack --in &lt;dir&gt; --out &lt;pak01_dir.vpk&gt; --source-build &lt;sha&gt;
///                 [--prefix &lt;p&gt;] [--json] [--verify]
///
/// The last link in the chain: plan -> batch -> overlay -> resourcecompiler ->
/// .vdata_c -> HERE -> addon VPK.
///
/// DESIGN, 2026-08-12:
///
///   - Archive writing stays in Deadlock.Format. CI enforces the layer
///     boundary, and Format already owns ValvePak; this command is a front end
///     over VpkWriter.CreateFromDirectory and touches no archive API itself.
///   - Entries are keyed RELATIVE to --in. Point it at the compiler's output
///     directory (game/citadel) and entries come out as `scripts/x.vdata_c`,
///     which is how the game asks for them. See the note on
///     CreateFromDirectory — marked [I], not confirmed against a running game.
///   - --source-build is REQUIRED, as in batch. D2: an artifact with no build
///     id is an unlabelled artifact, and a VPK is the most shippable artifact
///     this toolkit produces.
///   - --verify re-reads the archive through VpkIndex and checks every CRC32
///     against the independently computed one. Cheap, and it is the same
///     round-trip property format-smoke established.
///
/// It says "structurally valid", never "works" (D7). Nothing here has been
/// loaded by Deadlock.
/// </summary>
internal static class PackCommand
{
    public const string Usage = """
        dl-patch pack — build an addon VPK from a compiled tree

        usage:
          dl-patch pack --in <dir> --out <pak01_dir.vpk> --source-build <sha>
                        [--prefix <p>] [--json] [--verify]

        options:
          --in <dir>            directory to pack (required)
          --out <path>          VPK to write (required)
          --source-build <sha>  build the inputs came from (required)
          --prefix <p>          prepend a path prefix to every entry
          --verify              re-read the archive and check every CRC32
          --json                envelope on stdout
          -h, --help            this text

        entry paths:
          Keyed RELATIVE to --in, forward-slashed. Point --in at the
          compiler's output directory (game/citadel) and entries come out as
          scripts/<name>.vdata_c — the shape the game asks for.

        install:
          A mod is a VPK at Deadlock/game/citadel/addons/pak##_dir.vpk, ## from
          01-99, LOWER number = HIGHER priority. Requires a one-time
          gameinfo.gi SearchPaths edit. Whether Deadlock accepts a modded
          vdata this way is UNCONFIRMED — needs hardware.

        exit: 0 ok · 2 misuse · 4 input unreadable · 8 verification failed
        """;

    public static int Run(string[] args)
    {
        string? input = null, output = null, sourceBuild = null, prefix = null;
        bool json = false, verify = false;

        for (var i = 0; i < args.Length; i++)
        {
            switch (args[i])
            {
                case "-h":
                case "--help":
                    Console.Error.WriteLine(Usage);
                    return Exit.Ok;

                case "--in":
                    if (++i >= args.Length) return Misuse("--in needs a directory", json);
                    input = args[i];
                    break;

                case "--out":
                    if (++i >= args.Length) return Misuse("--out needs a path", json);
                    output = args[i];
                    break;

                case "--source-build":
                    if (++i >= args.Length) return Misuse("--source-build needs a value", json);
                    sourceBuild = args[i];
                    break;

                case "--prefix":
                    if (++i >= args.Length) return Misuse("--prefix needs a value", json);
                    prefix = args[i];
                    break;

                case "--verify":
                    verify = true;
                    break;

                case "--json":
                    json = true;
                    break;

                default:
                    return Misuse($"unknown argument: {args[i]}", json);
            }
        }

        if (input is null) return Misuse("--in is required", json);
        if (output is null) return Misuse("--out is required", json);
        if (sourceBuild is null) return Misuse("--source-build is required", json);

        ManifestResult result;
        try
        {
            result = VpkWriter.CreateFromDirectory(input, output, prefix);
        }
        catch (DirectoryNotFoundException ex)
        {
            return Fail(sourceBuild, ErrorCode.InputNotFound, ex.Message,
                        "check --in points at an existing directory",
                        PatchExit.InputUnreadable, json);
        }
        catch (InvalidOperationException ex)
        {
            return Fail(sourceBuild, ErrorCode.InputNotFound, ex.Message,
                        "the directory is empty; compile something into it first",
                        PatchExit.InputUnreadable, json);
        }
        catch (Exception ex)
        {
            return Fail(sourceBuild, ErrorCode.OutputUnwritable,
                        $"could not write {output}: {ex.GetType().Name}: {ex.Message}",
                        "check the output directory is writable",
                        PatchExit.InputUnreadable, json);
        }

        var entries = result.Entries
            .Select(e => new PackEntry
            {
                Path = e.Path,
                Length = e.Length,
                Crc32 = e.Crc32
            })
            .ToList();

        var data = new PackData
        {
            Input = input,
            Output = output,
            Prefix = prefix,
            FileCount = entries.Count,
            TotalBytes = entries.Sum(e => (long)e.Length),
            Verified = false,
            Entries = entries
        };

        if (verify)
        {
            // Round-trip: ValvePak's reported CRC32 against the one computed
            // independently on the way in. This is the property format-smoke
            // established; re-asserting it per archive costs almost nothing.
            try
            {
                var index = VpkIndex.Read(output);
                var byPath = index.Entries.ToDictionary(e => e.Path, StringComparer.Ordinal);
                var mismatches = new List<string>();

                foreach (var e in entries)
                {
                    if (!byPath.TryGetValue(e.Path, out var got))
                    {
                        mismatches.Add($"{e.Path}: missing on read-back");
                        continue;
                    }
                    if (got.Crc32 != e.Crc32)
                        mismatches.Add($"{e.Path}: crc32 {got.Crc32:X8} != {e.Crc32:X8}");
                    if (got.Length != e.Length)
                        mismatches.Add($"{e.Path}: length {got.Length} != {e.Length}");
                }

                if (mismatches.Count > 0)
                {
                    return Fail(sourceBuild, ErrorCode.VerifyFailed,
                        $"{mismatches.Count} entries failed verification: " +
                        string.Join("; ", mismatches.Take(5)),
                        "the archive does not read back as written; do not ship it",
                        PatchExit.VerifyFailed, json, data);
                }

                data = new PackData
                {
                    Input = data.Input,
                    Output = data.Output,
                    Prefix = data.Prefix,
                    FileCount = data.FileCount,
                    TotalBytes = data.TotalBytes,
                    Verified = true,
                    Entries = data.Entries
                };
            }
            catch (Exception ex)
            {
                return Fail(sourceBuild, ErrorCode.VerifyFailed,
                    $"could not re-read {output}: {ex.GetType().Name}: {ex.Message}",
                    "the archive was written but is not readable",
                    PatchExit.VerifyFailed, json, data);
            }
        }

        return Emit(data, sourceBuild, null, Exit.Ok, json);
    }

    private static int Fail(string sourceBuild, string code, string message, string fix,
                            int exitCode, bool json, PackData? data = null)
        => Emit(data ?? new PackData(), sourceBuild,
                new ToolError(code, message, fix), exitCode, json);

    private static int Emit(PackData data, string sourceBuild, ToolError? error, int code, bool json)
        => CommandIo.Emit(data, error, code, json, sourceBuild,
            body: () =>
            {
                foreach (var e in data.Entries)
                    Console.Error.WriteLine($"  {e.Path}  ({e.Length} bytes, crc32 {e.Crc32:X8})");
            },
            footer: () =>
            {
                if (error is not null) return;
                Console.Error.WriteLine(
                    $"wrote {data.Output} — {data.FileCount} files, {data.TotalBytes} bytes" +
                    (data.Verified ? ", verified" : "") + ", structurally valid");
            });

    private static int Misuse(string message, bool json)
        => CommandIo.Misuse<PackData>(message, json, Usage, "see 'dl-patch pack --help'");
}
