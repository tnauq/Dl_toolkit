using System.Globalization;
using System.Text.Json;

namespace Deadlock.Patch;

/// <summary>
/// One entry in a plan's <c>set</c> array.
///
/// <c>Expect</c> is MANDATORY (Q1, 2026-08-12) — a plan cannot be written
/// without stating what it believes the current value is. An explicit JSON
/// null opts out, which makes the hole deliberate and greppable rather than
/// accidental.
/// </summary>
public sealed record PlanSet(string Path, ScalarValue Value, ScalarValue? Expect, bool Guarded);

/// <summary>One file and the edits destined for it.</summary>
public sealed record PlanFile(string File, List<PlanSet> Sets);

/// <summary>A parsed, validated plan.</summary>
public sealed class Plan
{
    public const int SupportedVersion = 1;

    public string? Description { get; init; }
    public List<PlanFile> Files { get; init; } = new();

    /// <summary>
    /// Parses strictly: an unknown field or an unsupported version is REFUSED
    /// (Q10). A typo'd key that is silently ignored is how a mandatory guard
    /// gets dropped without anyone noticing, which would undo Q1 entirely.
    /// </summary>
    public static bool TryParse(string json, out Plan? plan, out string? error)
    {
        plan = null;
        error = null;

        JsonDocument doc;
        try
        {
            doc = JsonDocument.Parse(json, new JsonDocumentOptions
            {
                CommentHandling = JsonCommentHandling.Skip,
                AllowTrailingCommas = false
            });
        }
        catch (JsonException ex)
        {
            error = $"plan is not valid JSON: {ex.Message}";
            return false;
        }

        using (doc)
        {
            var root = doc.RootElement;
            if (root.ValueKind != JsonValueKind.Object)
            {
                error = "plan must be a JSON object";
                return false;
            }

            if (!Strict(root, new[] { "version", "description", "edits" }, "plan", out error))
                return false;

            if (!root.TryGetProperty("version", out var versionEl))
            {
                error = "plan is missing 'version'";
                return false;
            }

            if (versionEl.ValueKind != JsonValueKind.Number ||
                !versionEl.TryGetInt32(out var version))
            {
                error = "plan 'version' must be an integer";
                return false;
            }

            if (version != SupportedVersion)
            {
                error = $"plan version {version} is not supported; this build reads version {SupportedVersion}";
                return false;
            }

            string? description = null;
            if (root.TryGetProperty("description", out var descEl))
            {
                if (descEl.ValueKind != JsonValueKind.String)
                {
                    error = "plan 'description' must be a string";
                    return false;
                }
                description = descEl.GetString();
            }

            if (!root.TryGetProperty("edits", out var editsEl) ||
                editsEl.ValueKind != JsonValueKind.Array)
            {
                error = "plan is missing an 'edits' array";
                return false;
            }

            if (editsEl.GetArrayLength() == 0)
            {
                error = "plan 'edits' is empty; nothing to do";
                return false;
            }

            var files = new List<PlanFile>();
            var seenFiles = new HashSet<string>(StringComparer.Ordinal);
            var duplicateFiles = new List<string>();

            foreach (var fileEl in editsEl.EnumerateArray())
            {
                if (fileEl.ValueKind != JsonValueKind.Object)
                {
                    error = "every entry in 'edits' must be an object";
                    return false;
                }

                if (!Strict(fileEl, new[] { "file", "set" }, "edits entry", out error))
                    return false;

                if (!fileEl.TryGetProperty("file", out var fEl) ||
                    fEl.ValueKind != JsonValueKind.String)
                {
                    error = "every 'edits' entry needs a 'file' string";
                    return false;
                }

                var file = fEl.GetString()!;
                if (file.Length == 0)
                {
                    error = "'file' is empty";
                    return false;
                }

                // Q4 makes --out-root a separate tree; a path escaping the root
                // would write outside it. Refused rather than normalised.
                if (System.IO.Path.IsPathRooted(file) || file.Contains("..", StringComparison.Ordinal))
                {
                    error = $"'file' must be a relative path inside the root, got: {file}";
                    return false;
                }

                // Q11: one entry per file. Two entries naming the same file is
                // a plan that wants merge semantics, and merging is out of scope.
                if (!seenFiles.Add(file)) duplicateFiles.Add(file);

                if (!fileEl.TryGetProperty("set", out var setEl) ||
                    setEl.ValueKind != JsonValueKind.Array ||
                    setEl.GetArrayLength() == 0)
                {
                    error = $"'{file}' needs a non-empty 'set' array";
                    return false;
                }

                var sets = new List<PlanSet>();
                var seenPaths = new HashSet<string>(StringComparer.Ordinal);
                var duplicatePaths = new List<string>();

                foreach (var s in setEl.EnumerateArray())
                {
                    if (s.ValueKind != JsonValueKind.Object)
                    {
                        error = $"every 'set' entry in '{file}' must be an object";
                        return false;
                    }

                    if (!Strict(s, new[] { "path", "value", "expect" }, $"set entry in '{file}'", out error))
                        return false;

                    if (!s.TryGetProperty("path", out var pEl) ||
                        pEl.ValueKind != JsonValueKind.String)
                    {
                        error = $"a 'set' entry in '{file}' has no 'path' string";
                        return false;
                    }

                    var path = pEl.GetString()!.Trim();
                    if (path.Length == 0 || path.Split('.').Any(seg => seg.Length == 0))
                    {
                        error = $"'{file}': path is empty or has an empty segment: '{path}'";
                        return false;
                    }

                    // Q5: two edits to one path is an error, not last-wins.
                    if (!seenPaths.Add(path)) duplicatePaths.Add(path);

                    if (!s.TryGetProperty("value", out var vEl))
                    {
                        error = $"'{file}' path '{path}' has no 'value'";
                        return false;
                    }

                    if (!TryScalar(vEl, out var value, out var vErr))
                    {
                        error = $"'{file}' path '{path}': value {vErr}";
                        return false;
                    }

                    // Mandatory. Absent is an error; explicit null is the opt-out.
                    if (!s.TryGetProperty("expect", out var eEl))
                    {
                        error = $"'{file}' path '{path}' has no 'expect'. " +
                                "Guards are mandatory; use \"expect\": null to opt out deliberately";
                        return false;
                    }

                    ScalarValue? expect = null;
                    var guarded = eEl.ValueKind != JsonValueKind.Null;
                    if (guarded)
                    {
                        if (!TryScalar(eEl, out expect, out var eErr))
                        {
                            error = $"'{file}' path '{path}': expect {eErr}";
                            return false;
                        }
                    }

                    sets.Add(new PlanSet(path, value!, expect, guarded));
                }

                if (duplicatePaths.Count > 0)
                {
                    error = $"'{file}' sets the same path more than once: " +
                            string.Join(", ", duplicatePaths.Distinct().OrderBy(x => x, StringComparer.Ordinal));
                    return false;
                }

                files.Add(new PlanFile(file, sets));
            }

            if (duplicateFiles.Count > 0)
            {
                error = "plan lists the same file more than once: " +
                        string.Join(", ", duplicateFiles.Distinct().OrderBy(x => x, StringComparer.Ordinal)) +
                        ". Use one entry per file; merging two plans is not supported";
                return false;
            }

            plan = new Plan { Description = description, Files = files };
            return true;
        }
    }

    /// <summary>Rejects any property outside the accepted set.</summary>
    private static bool Strict(JsonElement obj, string[] allowed, string where, out string? error)
    {
        error = null;
        foreach (var prop in obj.EnumerateObject())
        {
            if (!allowed.Contains(prop.Name, StringComparer.Ordinal))
            {
                error = $"unknown field '{prop.Name}' in {where}; accepted: {string.Join(", ", allowed)}";
                return false;
            }
        }
        return true;
    }

    /// <summary>
    /// JSON is typed, so no inference is needed here — unlike argv, where
    /// quoting is the only way to force a string. A JSON string is a string.
    /// </summary>
    private static bool TryScalar(JsonElement el, out ScalarValue? value, out string? error)
    {
        value = null;
        error = null;

        switch (el.ValueKind)
        {
            case JsonValueKind.True:
                value = new ScalarValue(ScalarKind.Bool, true, "true");
                return true;

            case JsonValueKind.False:
                value = new ScalarValue(ScalarKind.Bool, false, "false");
                return true;

            case JsonValueKind.String:
                var s = el.GetString()!;
                value = new ScalarValue(ScalarKind.String, s, s);
                return true;

            case JsonValueKind.Number:
                var raw = el.GetRawText();
                if (!raw.Contains('.', StringComparison.Ordinal) &&
                    !raw.Contains('e', StringComparison.OrdinalIgnoreCase) &&
                    el.TryGetInt64(out var l))
                {
                    value = new ScalarValue(ScalarKind.Long, l, raw);
                    return true;
                }
                if (el.TryGetDouble(out var d))
                {
                    value = new ScalarValue(ScalarKind.Double, d, raw);
                    return true;
                }
                error = $"number '{raw}' is out of range";
                return false;

            default:
                error = $"must be a number, string or bool, got {el.ValueKind}";
                return false;
        }
    }
}

/// <summary>
/// Guard comparison (Q2).
///
/// Numbers are compared AFTER 6dp normalisation, because that is what the file
/// will contain once VRF has round-tripped it. Comparing raw would make a guard
/// on a high-precision float fail against a file the tool itself wrote — see
/// the float sweep (probe-floats 2026-08-11): two literals in abilities.vdata
/// carry more than 6dp, so this is a live case, not a hypothetical.
///
/// Bools and strings compare exactly. A type disagreement is a mismatch, not
/// an error: the field changing type between builds is exactly the drift a
/// guard exists to catch.
/// </summary>
public static class Guard
{
    public const int DecimalPlaces = 6;

    public static bool Matches(object? existing, ScalarValue expect, out string actual)
    {
        actual = Kv3Document.Show(existing);

        switch (existing)
        {
            case bool b:
                return expect.Kind == ScalarKind.Bool && b == (bool)expect.Value;

            case string s:
                return expect.Kind == ScalarKind.String &&
                       string.Equals(s, (string)expect.Value, StringComparison.Ordinal);

            case double or float or sbyte or byte or short or ushort
                 or int or uint or long or ulong:
                if (expect.Kind is not (ScalarKind.Double or ScalarKind.Long)) return false;
                var have = Convert.ToDouble(existing, CultureInfo.InvariantCulture);
                var want = expect.Kind == ScalarKind.Long
                    ? (double)(long)expect.Value
                    : (double)expect.Value;
                return string.Equals(Normalize(have), Normalize(want), StringComparison.Ordinal);

            default:
                return false;
        }
    }

    private static string Normalize(double d)
        => d.ToString("F" + DecimalPlaces.ToString(CultureInfo.InvariantCulture),
                      CultureInfo.InvariantCulture);
}
