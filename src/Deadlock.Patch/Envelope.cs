using System.Text.Json.Serialization;

namespace Deadlock.Patch;

/// <summary>
/// The dl-patch PAYLOAD — what goes in <c>Envelope&lt;T&gt;.Data</c>.
///
/// FOLDED 2026-08-12. This file used to declare a second, local copy of the
/// envelope and the exit codes, because Deadlock.Contracts' type names had not
/// been read. They have been (dump-contracts run, 2026-08-12), so the outer
/// shape and the shared codes now come from Contracts and only the
/// tool-specific parts remain here.
///
/// Shape change, stated because it is a breaking one for any consumer:
/// the fields below used to sit at the TOP level of the JSON. They now sit
/// under <c>data</c>, and the single <c>error</c> string has become the
/// standard <c>errors</c> array of {code, message, fix}. Nothing outside this
/// repo consumes it yet, which is why the fold is cheap today and would not
/// have been later.
/// </summary>
public sealed class PatchData
{
    [JsonPropertyName("dry_run")] public bool DryRun { get; init; }
    [JsonPropertyName("input")] public string? Input { get; init; }
    [JsonPropertyName("output")] public string? Output { get; init; }
    [JsonPropertyName("applied")] public int Applied { get; init; }
    [JsonPropertyName("failed")] public int Failed { get; init; }
    [JsonPropertyName("edits")] public List<EditReport> Edits { get; init; } = new();
}

public sealed class EditReport
{
    // NOTE: the factory below is called Of, not From — `From` is already a
    // property name here and C# will not allow both on one type (CS0102,
    // caught by the build 2026-08-09).
    [JsonPropertyName("path")] public string Path { get; set; } = "";
    [JsonPropertyName("from")] public string? From { get; set; }
    [JsonPropertyName("to")] public string To { get; set; } = "";
    [JsonPropertyName("ok")] public bool Ok { get; set; }
    [JsonPropertyName("error")] public string? Error { get; set; }

    public static EditReport Of(EditResult r) => new()
    {
        Path = r.Path,
        From = r.From,
        To = r.To,
        Ok = r.Ok,
        Error = r.Error
    };
}

/// <summary>
/// Exit codes ABOVE the shared range.
///
/// <c>Deadlock.Contracts.Exit</c> owns 0–3 and they mean the same thing in
/// every tool: 0 ok, 1 expected failure, 2 misuse, 3 missing dependency.
/// 4 upward is a per-tool extension range — a caller that only understands the
/// shared codes still reads "nonzero, and not misuse", which is the useful
/// part. dl-patch does not currently use code 1; a future <c>--check</c> mode
/// is what that code is for.
/// </summary>
public static class PatchExit
{
    public const int InputUnreadable = 4;
    public const int PathNotFound = 5;
    public const int TypeMismatch = 6;
}

/// <summary>
/// Error codes carried in <c>ToolError.Code</c>. Stable strings — an agent
/// branches on these rather than on message text.
/// </summary>
public static class ErrorCode
{
    public const string Misuse = "misuse";
    public const string InputNotFound = "input_not_found";
    public const string InputUnreadable = "input_unreadable";
    public const string OutputUnwritable = "output_unwritable";
    public const string PathNotFound = "path_not_found";
    public const string TypeMismatch = "type_mismatch";
}
