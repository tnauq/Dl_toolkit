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
}
