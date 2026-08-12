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
/// </summary>
public sealed class PatchData
{
    [JsonPropertyName("mode")] public string Mode { get; init; } = "set";
    [JsonPropertyName("dry_run")] public bool DryRun { get; init; }
    [JsonPropertyName("input")] public string? Input { get; init; }
    [JsonPropertyName("output")] public string? Output { get; init; }
    [JsonPropertyName("applied")] public int Applied { get; init; }
    [JsonPropertyName("failed")] public int Failed { get; init; }
    [JsonPropertyName("edits")] public List<EditReport> Edits { get; init; } = new();
}

/// <summary>
/// Batch payload.
///
/// Every file named in the plan appears in <c>Files</c> whether or not it
/// changed (Q16), so the envelope's shape depends on the PLAN and never on the
/// content of the tree. That makes "files[] matches the plan's file list" an
/// assertable invariant, and it makes two envelopes from different builds
/// directly diffable.
/// </summary>
public sealed class BatchData
{
    [JsonPropertyName("mode")] public string Mode { get; init; } = "batch";
    [JsonPropertyName("dry_run")] public bool DryRun { get; init; }
    [JsonPropertyName("plan")] public string? PlanPath { get; init; }
    [JsonPropertyName("description")] public string? Description { get; init; }
    [JsonPropertyName("root")] public string? Root { get; init; }
    [JsonPropertyName("out_root")] public string? OutRoot { get; init; }
    [JsonPropertyName("files_total")] public int FilesTotal { get; init; }
    [JsonPropertyName("applied")] public int Applied { get; init; }
    [JsonPropertyName("skipped")] public int Skipped { get; init; }
    [JsonPropertyName("failed")] public int Failed { get; init; }
    [JsonPropertyName("files")] public List<BatchFileReport> Files { get; init; } = new();
}

public sealed class BatchFileReport
{
    [JsonPropertyName("file")] public string File { get; set; } = "";
    [JsonPropertyName("applied")] public int Applied { get; set; }
    [JsonPropertyName("skipped")] public int Skipped { get; set; }
    [JsonPropertyName("failed")] public int Failed { get; set; }
    [JsonPropertyName("written")] public bool Written { get; set; }
    [JsonPropertyName("edits")] public List<EditReport> Edits { get; set; } = new();
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

    /// <summary>Null when unguarded, otherwise the value the plan expected.</summary>
    [JsonPropertyName("expected")] public string? Expected { get; set; }

    /// <summary>True when the value already equalled the target (Q16).</summary>
    [JsonPropertyName("noop")] public bool Noop { get; set; }

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
/// diff payload. Differences are a RESULT: `ok` stays true and `errors` stays
/// empty even when the files differ. The exit code carries the verdict.
/// </summary>
public sealed class DiffData
{
    [JsonPropertyName("mode")] public string Mode { get; init; } = "diff";
    [JsonPropertyName("old")] public string? Old { get; init; }
    [JsonPropertyName("new")] public string? New { get; init; }
    [JsonPropertyName("old_paths")] public int OldPaths { get; init; }
    [JsonPropertyName("new_paths")] public int NewPaths { get; init; }
    [JsonPropertyName("added")] public int Added { get; init; }
    [JsonPropertyName("removed")] public int Removed { get; init; }
    [JsonPropertyName("changed")] public int Changed { get; init; }
    [JsonPropertyName("retyped")] public int Retyped { get; init; }
    [JsonPropertyName("total")] public int Total { get; init; }
    [JsonPropertyName("truncated")] public bool Truncated { get; init; }
    [JsonPropertyName("entries")] public List<DiffEntry> Entries { get; init; } = new();
}

public sealed class DiffEntry
{
    /// <summary>added, removed, changed, or retyped.</summary>
    [JsonPropertyName("change")] public string Change { get; set; } = "";
    [JsonPropertyName("path")] public string Path { get; set; } = "";
    [JsonPropertyName("from")] public string? From { get; set; }
    [JsonPropertyName("to")] public string? To { get; set; }
    [JsonPropertyName("kind")] public string? Kind { get; set; }
}

/// <summary>
/// Exit codes ABOVE the shared range.
///
/// <c>Deadlock.Contracts.Exit</c> owns 0–3 and they mean the same thing in
/// every tool: 0 ok, 1 expected failure, 2 misuse, 3 missing dependency.
/// 4 upward is a per-tool extension range — a caller that only understands the
/// shared codes still reads "nonzero, and not misuse", which is the useful
/// part.
///
/// Code 1 (ExpectedFailure) is used by `diff` for "files differ" — a completed
/// run whose assertion did not hold, which is precisely its shared meaning.
/// batch does not use it; a future <c>--check</c> mode is what it would use.
/// </summary>
public static class PatchExit
{
    public const int InputUnreadable = 4;
    public const int PathNotFound = 5;
    public const int TypeMismatch = 6;

    /// <summary>
    /// A guard did not match, or a guarded path is gone (Q8, Q9). Distinct
    /// from 5 and 6 because it means something different in kind: the plan and
    /// the file are both fine, and the BUILD moved underneath them. An agent
    /// seeing 7 should re-derive the plan, not fix its syntax.
    /// </summary>
    public const int GuardFailed = 7;
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
    public const string GuardFailed = "guard_failed";
    public const string PlanInvalid = "plan_invalid";
    public const string TooManyFiles = "too_many_files";
}
