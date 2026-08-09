using System.Text.Json;
using System.Text.Json.Serialization;

namespace Deadlock.Patch;

/// <summary>
/// Mirrors the Deadlock.Contracts envelope shape locally. See the note in the
/// csproj: the real types were not read, so this is a placeholder to be folded
/// back, not a second standard.
/// </summary>
public sealed class Envelope
{
    [JsonPropertyName("ok")] public bool Ok { get; set; }
    [JsonPropertyName("tool")] public string Tool { get; set; } = "dl-patch";
    [JsonPropertyName("version")] public string Version { get; set; } = "0.1.0";
    [JsonPropertyName("dryRun")] public bool DryRun { get; set; }
    [JsonPropertyName("input")] public string? Input { get; set; }
    [JsonPropertyName("output")] public string? Output { get; set; }
    [JsonPropertyName("applied")] public int Applied { get; set; }
    [JsonPropertyName("failed")] public int Failed { get; set; }
    [JsonPropertyName("edits")] public List<EditReport> Edits { get; set; } = new();
    [JsonPropertyName("error")] public string? Error { get; set; }

    private static readonly JsonSerializerOptions Opts = new()
    {
        WriteIndented = true,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull
    };

    public string ToJson() => JsonSerializer.Serialize(this, Opts);
}

public sealed class EditReport
{
    [JsonPropertyName("path")] public string Path { get; set; } = "";
    [JsonPropertyName("from")] public string? From { get; set; }
    [JsonPropertyName("to")] public string To { get; set; } = "";
    [JsonPropertyName("ok")] public bool Ok { get; set; }
    [JsonPropertyName("error")] public string? Error { get; set; }

    public static EditReport From(EditResult r) => new()
    {
        Path = r.Path,
        From = r.From,
        To = r.To,
        Ok = r.Ok,
        Error = r.Error
    };
}

/// <summary>Exit codes. Mirrors the convention already used by dl-extract.</summary>
public static class Exit
{
    public const int Ok = 0;
    public const int Misuse = 2;
    public const int MissingDependency = 3;
    public const int InputUnreadable = 4;
    public const int PathNotFound = 5;
    public const int TypeMismatch = 6;
}
