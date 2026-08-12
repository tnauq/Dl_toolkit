using System.IO.Hashing;
using System.Text;
using System.Text.Json.Serialization;
using SteamDatabase.ValvePak;

namespace Deadlock.Format;

/// <summary>
/// One file as written, with its checksum computed INDEPENDENTLY of ValvePak.
/// The whole point: if this crc32 matches the one ValvePak reports on read-back,
/// then PackageEntry.CRC32 means what dl-diff assumes it means.
/// </summary>
public sealed record ManifestEntry(
    [property: JsonPropertyName("path")]   string Path,
    [property: JsonPropertyName("length")] uint Length,
    [property: JsonPropertyName("crc32")]  uint Crc32);

public sealed record ManifestResult(
    [property: JsonPropertyName("output")]  string Output,
    [property: JsonPropertyName("entries")] IReadOnlyList<ManifestEntry> Entries);

public static class VpkWriter
{
    /// <summary>
    /// Deterministic synthetic content — same bytes every run, so the smoke
    /// test's determinism check is meaningful rather than accidental.
    /// </summary>
    private static readonly (string Path, string Body)[] Files =
    {
        ("root.txt",                  "root file\n"),
        ("scripts/hero.vdata",        "{ hero = \"abrams\" max_health = 800 }\n"),
        ("scripts/item.vdata",        "{ item = \"grit\" cost = 800 }\n"),
        ("materials/dev/grid.vmat",   "// placeholder material\n"),
        ("maps/greybox/lane.vmap",    "// placeholder map\n"),
    };

    /// <summary>
    /// Build a VPK from synthetic content and return what was written.
    /// No game files involved — this exists so the Format layer can be
    /// exercised end to end before any fixture exists.
    /// </summary>
    public static ManifestResult CreateSynthetic(string outputPath)
    {
        var dir = System.IO.Path.GetDirectoryName(outputPath);
        if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);

        using var package = new Package();

        var manifest = new List<ManifestEntry>();
        foreach (var (path, body) in Files)
        {
            var bytes = Encoding.UTF8.GetBytes(body);
            package.AddFile(path, bytes);
            manifest.Add(new ManifestEntry(
                Path: path,
                Length: (uint)bytes.Length,
                Crc32: Crc32.HashToUInt32(bytes)));
        }

        package.Write(outputPath);

        return new ManifestResult(
            Output: outputPath,
            Entries: manifest.OrderBy(e => e.Path, StringComparer.Ordinal).ToList());
    }

    /// <summary>
    /// Pack every file under <paramref name="root"/> into a VPK, keyed by path
    /// RELATIVE to that root. Added 2026-08-12 for `dl-patch pack`.
    ///
    /// WHY RELATIVE-TO-ROOT. A Deadlock addon VPK lives at
    /// citadel/addons/pak##_dir.vpk and is mounted as a search path alongside
    /// the `citadel` game path declared in gameinfo.gi. Entries therefore have
    /// to be expressed the way the game asks for them — `scripts/heroes.vdata_c`,
    /// not `citadel/scripts/...` and not an absolute path. Pointing this at the
    /// compiler's own output directory (game/citadel) produces exactly that,
    /// because the compiler already writes to DEFAULT_WRITE_PATH in that shape.
    ///
    /// `[I]` — consistent with how gameinfo declares its mounts and with where
    /// resourcecompiler writes, but NOT confirmed against a running game. Use
    /// <paramref name="prefix"/> if a real addon turns out to need one.
    ///
    /// Separators are normalised to '/' because VPK paths are forward-slashed
    /// and a Windows runner would otherwise write backslashed keys that the
    /// game never asks for.
    /// </summary>
    public static ManifestResult CreateFromDirectory(
        string root, string outputPath, string? prefix = null)
    {
        if (!Directory.Exists(root))
            throw new DirectoryNotFoundException($"input directory not found: {root}");

        var outDir = System.IO.Path.GetDirectoryName(outputPath);
        if (!string.IsNullOrEmpty(outDir)) Directory.CreateDirectory(outDir);

        // Sorted so the archive, and therefore its bytes, are deterministic.
        var files = Directory
            .EnumerateFiles(root, "*", SearchOption.AllDirectories)
            .OrderBy(f => f, StringComparer.Ordinal)
            .ToList();

        if (files.Count == 0)
            throw new InvalidOperationException($"no files under {root}");

        using var package = new Package();
        var manifest = new List<ManifestEntry>();

        foreach (var file in files)
        {
            var relative = System.IO.Path
                .GetRelativePath(root, file)
                .Replace('\\', '/');

            if (!string.IsNullOrEmpty(prefix))
                relative = prefix.TrimEnd('/') + "/" + relative;

            var bytes = File.ReadAllBytes(file);
            package.AddFile(relative, bytes);
            manifest.Add(new ManifestEntry(
                Path: relative,
                Length: (uint)bytes.Length,
                Crc32: Crc32.HashToUInt32(bytes)));
        }

        package.Write(outputPath);

        return new ManifestResult(
            Output: outputPath,
            Entries: manifest.OrderBy(e => e.Path, StringComparer.Ordinal).ToList());
    }
}
