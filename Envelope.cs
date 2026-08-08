using System.Text.Json;
using System.Text.Json.Serialization;

namespace Deadlock.Contracts;

/// <summary>
/// The outer shape every tool emits. See TOOLING.md section 4.
/// Consumers parse this once and never special-case a tool.
/// </summary>
public sealed class Envelope<T>
{
    [JsonPropertyName("tool")]        public string Tool { get; init; } = "";
    [JsonPropertyName("version")]     public string Version { get; init; } = "0.1.0";
    [JsonPropertyName("pinned_build")] public string? PinnedBuild { get; init; }
    [JsonPropertyName("ok")]          public bool Ok { get; init; }
    [JsonPropertyName("data")]        public T? Data { get; init; }
    [JsonPropertyName("warnings")]    public List<string> Warnings { get; init; } = new();
    [JsonPropertyName("errors")]      public List<ToolError> Errors { get; init; } = new();
}

public sealed record ToolError(
    [property: JsonPropertyName("code")]    string Code,
    [property: JsonPropertyName("message")] string Message,
    [property: JsonPropertyName("fix")]     string Fix);

/// <summary>
/// Exit codes are part of the interface. TOOLING.md section 3.
/// </summary>
public static class Exit
{
    public const int Ok = 0;
    public const int ExpectedFailure = 1;   // assertion failed, --check found a diff
    public const int Misuse = 2;            // bad arguments
    public const int MissingDependency = 3; // no fixture, no toolchain
}

public static class Json
{
    /// <summary>
    /// Deterministic by construction: indented for diffability, and callers are
    /// responsible for sorting collections BEFORE serialising. System.Text.Json
    /// preserves insertion order, so ordering is a producer obligation.
    /// </summary>
    public static readonly JsonSerializerOptions Options = new()
    {
        WriteIndented = true,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    public static void ToStdout<T>(Envelope<T> envelope)
        => Console.Out.WriteLine(JsonSerializer.Serialize(envelope, Options));
}
