using System.Globalization;

namespace Deadlock.Patch;

/// <summary>
/// One scalar assignment. Parsed from argv in v1; from a plan file in batch.
/// The batch front end must produce this same type — see TOOLING-dl-patch.md.
/// Nothing in this file may reach into argv.
/// </summary>
public sealed record Edit(string Path, ScalarValue Value)
{
    /// <summary>
    /// Parses "dotted.path=value". Splits on the FIRST '=' only, so string
    /// values may contain '='.
    /// </summary>
    public static bool TryParse(string arg, out Edit? edit, out string? error)
    {
        edit = null;
        error = null;

        var i = arg.IndexOf('=');
        if (i <= 0)
        {
            error = $"--set expects <dotted.path>=<value>, got: {arg}";
            return false;
        }

        var path = arg[..i].Trim();
        var raw = arg[(i + 1)..];

        if (path.Length == 0)
        {
            error = $"--set has an empty path: {arg}";
            return false;
        }

        if (path.Split('.').Any(s => s.Length == 0))
        {
            error = $"--set path has an empty segment: {path}";
            return false;
        }

        edit = new Edit(path, ScalarValue.Parse(raw));
        return true;
    }
}

public enum ScalarKind
{
    Bool,
    Long,
    Double,
    String
}

/// <summary>
/// A scalar the user asked for, before it meets the document.
/// </summary>
/// <remarks>
/// Inference rules, stated because they are a contract and not an accident:
///   true/false            -> Bool
///   /^-?\d+$/             -> Long
///   parses as a double    -> Double
///   anything else         -> String
///   "quoted"              -> String, ALWAYS, quotes stripped
///
/// The quote escape exists so a value that looks numeric can still be written
/// as a string. Without it there is no way to set a key to the string "1".
///
/// Inference is only a starting point: the document's existing type wins where
/// they disagree and a conversion is safe. See Kv3Document.Apply.
///
/// NOTE: batch does NOT use this parser. A plan is JSON, which is already
/// typed, so no inference and no quote escape are needed there.
/// </remarks>
public sealed record ScalarValue(ScalarKind Kind, object Value, string Raw)
{
    public static ScalarValue Parse(string raw)
    {
        if (raw.Length >= 2 && raw[0] == '"' && raw[^1] == '"')
        {
            var inner = raw[1..^1];
            return new ScalarValue(ScalarKind.String, inner, raw);
        }

        if (string.Equals(raw, "true", StringComparison.OrdinalIgnoreCase))
            return new ScalarValue(ScalarKind.Bool, true, raw);

        if (string.Equals(raw, "false", StringComparison.OrdinalIgnoreCase))
            return new ScalarValue(ScalarKind.Bool, false, raw);

        if (long.TryParse(raw, NumberStyles.Integer, CultureInfo.InvariantCulture, out var l))
            return new ScalarValue(ScalarKind.Long, l, raw);

        if (double.TryParse(raw, NumberStyles.Float, CultureInfo.InvariantCulture, out var d))
            return new ScalarValue(ScalarKind.Double, d, raw);

        return new ScalarValue(ScalarKind.String, raw, raw);
    }

    public override string ToString() => Kind switch
    {
        ScalarKind.Bool => ((bool)Value) ? "true" : "false",
        ScalarKind.Long => ((long)Value).ToString(CultureInfo.InvariantCulture),
        ScalarKind.Double => ((double)Value).ToString("R", CultureInfo.InvariantCulture),
        _ => (string)Value
    };
}

/// <summary>
/// Why an edit failed, as a VALUE rather than as prose.
///
/// ADDED 2026-08-13, fixing a real hazard. Both front ends previously decided
/// which exit code to return by string-matching the error message:
///
///     r.Error.Contains("path not found")   ->  exit 5 rather than 6
///
/// That contradicts the project's own principle — agents branch on codes, not
/// prose — and it means REWORDING AN ERROR MESSAGE SILENTLY CHANGES EXIT-CODE
/// BEHAVIOUR. The message stays for humans; nothing behavioural reads it now.
/// </summary>
public enum EditFailure
{
    /// <summary>The edit succeeded.</summary>
    None = 0,

    /// <summary>A path segment does not exist in this document.</summary>
    PathNotFound,

    /// <summary>The path resolves, but not to a plain scalar (block or array).</summary>
    NotAScalar,

    /// <summary>A flagged value — resource_name:, subclass:, panorama:.</summary>
    Flagged,

    /// <summary>The document's existing type refuses the supplied value.</summary>
    TypeMismatch,

    /// <summary>The document itself is malformed, e.g. no root object.</summary>
    Malformed
}

/// <summary>
/// What happened to one edit. Reported whether or not it succeeded.
///
/// <c>Failure</c> is the machine-readable reason and is what callers branch on.
/// <c>Error</c> is the human sentence and carries no behaviour.
/// </summary>
public sealed record EditResult(
    string Path,
    string? From,
    string To,
    bool Ok,
    string? Error,
    EditFailure Failure = EditFailure.None);
