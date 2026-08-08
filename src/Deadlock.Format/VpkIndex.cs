using System.Text.Json.Serialization;
using SteamDatabase.ValvePak;

namespace Deadlock.Format;

/// <summary>
/// One VPK directory entry. Everything here comes from the INDEX — no body is
/// read. CRC32 is what makes dl-diff cheap: change detection never decodes.
/// </summary>
public sealed record VpkEntry(
    [property: JsonPropertyName("path")]        string Path,
    [property: JsonPropertyName("type")]        string Type,
    [property: JsonPropertyName("length")]      uint Length,
    [property: JsonPropertyName("crc32")]       uint Crc32,
    [property: JsonPropertyName("archive_index")] ushort ArchiveIndex);

public sealed record VpkIndexResult(
    [property: JsonPropertyName("source")]      string Source,
    [property: JsonPropertyName("entry_count")] int EntryCount,
    [property: JsonPropertyName("types")]       IReadOnlyList<string> Types,
    [property: JsonPropertyName("entries")]     IReadOnlyList<VpkEntry> Entries);

public static class VpkIndex
{
    /// <summary>
    /// Read a VPK directory. Opens pak01_dir.vpk-style archives only; numbered
    /// data files are not openable (FINDINGS.md, VPK access).
    /// </summary>
    /// <param name="includeEntries">
    /// False returns counts and types only — enough for a smoke test or a
    /// summary, without materialising thousands of records.
    /// </param>
    public static VpkIndexResult Read(string path, bool includeEntries = true)
    {
        using var package = new Package();
        package.Read(path);

        var types = package.Entries.Keys.OrderBy(k => k, StringComparer.Ordinal).ToList();

        // Sorted at the producer. Deterministic output is a contract, and
        // ValvePak's dictionary order is not guaranteed stable across versions.
        var entries = includeEntries
            ? package.Entries
                .SelectMany(group => group.Value.Select(e => new VpkEntry(
                    Path: e.GetFullPath(),
                    Type: group.Key,
                    Length: e.TotalLength,
                    Crc32: e.CRC32,
                    ArchiveIndex: e.ArchiveIndex)))
                .OrderBy(e => e.Path, StringComparer.Ordinal)
                .ToList()
            : new List<VpkEntry>();

        var count = package.Entries.Sum(g => g.Value.Count);

        return new VpkIndexResult(
            Source: System.IO.Path.GetFileName(path),
            EntryCount: count,
            Types: types,
            Entries: entries);
    }
}
