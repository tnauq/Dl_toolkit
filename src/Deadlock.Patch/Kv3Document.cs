using System.Globalization;
using ValveResourceFormat.Serialization.KeyValues;

namespace Deadlock.Patch;

/// <summary>
/// Wraps VRF's KV3 object model. THE ONLY FILE THAT TOUCHES IT.
///
/// Written against the API as actually dumped by probe-kv3 2026-08-09
/// (kv3-surface.txt, live-inspect.txt), not from expectation. The relevant
/// facts, all [V-CI]:
///
///   KV3File.Root            -> KVObject, settable
///   KVObject.Properties     -> Dictionary&lt;string, KVValue&gt;. The PROPERTY is
///                              readonly, but the dictionary is mutable, so
///                              in-place assignment is available.
///   KVObject.IsArray        -> arrays are KVObjects too; v1 refuses them
///   KVValue.Type/.Flag      -> readonly; .Type is ValveKeyValue.KVValueType,
///                              which lives in a DIFFERENT assembly
///   KVValue.Value           -> readonly object; a nested block boxes a KVObject
///   ctor (Type, Flag, Value)
///   KVValue is a STRUCT     -> `KVValue?` means Nullable&lt;KVValue&gt;, NOT a
///                              nullable reference. Writing `out KVValue?` and
///                              then reaching for .Flag/.Type gives seven
///                              CS1061s plus a CS0184 saying an `is KVObject`
///                              test can never be true, because `.Value` binds
///                              to Nullable.Value. Declare it plain and
///                              initialise with `default`. (Build 2026-08-12.)
///
/// Design consequence worth stating: we never construct a KVValueType, we
/// REUSE the existing one along with its Flag. That preserves typed prefixes
/// such as resource_name: for free, and means this file names no enum member
/// it has not verified. Classification is done on the runtime type of
/// .Value — bool, long, double, string — which the dump confirms directly.
///
/// CHANGED 2026-08-13: every failure path now reports a structured
/// EditFailure alongside its human message, so callers stop string-matching
/// error prose to pick an exit code. See the note on EditFailure in Edit.cs.
///
/// CHANGED 2026-08-12 for batch: traversal is factored into Resolve, and
/// TryRead exposes the current value WITHOUT mutating. Guard evaluation needs
/// to read every target before anything is applied, so read and write can no
/// longer be the same operation. Apply's behaviour and its error strings are
/// unchanged — patch-smoke asserts on them.
/// </summary>
public sealed class Kv3Document
{
    private readonly KV3File _file;

    private Kv3Document(KV3File file) => _file = file;

    public static Kv3Document Load(string path)
    {
        var file = KeyValues3.ParseKVFile(path)
                   ?? throw new InvalidDataException($"parser returned null for {path}");
        return new Kv3Document(file);
    }

    public void Save(string path)
    {
        var dir = System.IO.Path.GetDirectoryName(path);
        if (!string.IsNullOrEmpty(dir)) Directory.CreateDirectory(dir);
        File.WriteAllText(path, _file.ToString());
    }

    /// <summary>Serialised form, for callers that stage in memory (batch).</summary>
    public string Serialize() => _file.ToString();

    /// <summary>
    /// Walks a dotted path to its leaf without changing anything.
    /// Returns false with a populated <paramref name="error"/> for any miss.
    /// </summary>
    private bool Resolve(string path, out KVObject? parent, out string leaf,
                         out KVValue existing, out string? error, out EditFailure failure)
    {
        parent = null;
        existing = default;
        error = null;
        failure = EditFailure.None;

        var segments = path.Split('.');
        leaf = segments[^1];

        var node = _file.Root;
        if (node is null)
        {
            error = "document has no root object";
            failure = EditFailure.Malformed;
            return false;
        }

        for (var i = 0; i < segments.Length - 1; i++)
        {
            var seg = segments[i];
            if (!node.Properties.TryGetValue(seg, out var childValue))
            {
                error = $"path not found: no key '{seg}' at '{string.Join('.', segments[..(i + 1)])}'";
                failure = EditFailure.PathNotFound;
                return false;
            }

            if (childValue.Value is not KVObject childObj)
            {
                error = $"path traverses a scalar: '{seg}' is a value, not a block";
                failure = EditFailure.NotAScalar;
                return false;
            }

            if (childObj.IsArray)
            {
                error = $"'{seg}' is an array; v1 does not address array elements";
                failure = EditFailure.NotAScalar;
                return false;
            }

            node = childObj;
        }

        if (!node.Properties.TryGetValue(leaf, out var found))
        {
            error = $"path not found: no key '{leaf}'";
            failure = EditFailure.PathNotFound;
            return false;
        }

        parent = node;
        existing = found;
        return true;
    }

    /// <summary>
    /// Reads the current scalar at a path. Used by batch to evaluate every
    /// guard before any edit is applied. Blocks, arrays and flagged values are
    /// refused here for the same reasons Apply refuses them — a guard that
    /// passed on something Apply would then reject is worse than no guard.
    /// </summary>
    public bool TryRead(string path, out object? value, out string? error,
                        out EditFailure failure)
    {
        value = null;

        if (!Resolve(path, out _, out var leaf, out var existing, out error, out failure))
            return false;

        if (existing.Value is KVObject)
        {
            error = $"'{leaf}' is a block or array; v1 sets scalars only";
            failure = EditFailure.NotAScalar;
            return false;
        }

        if (existing.Flag != KVFlag.None)
        {
            error = $"'{leaf}' is a {existing.Flag} value; v1 sets plain scalars only";
            failure = EditFailure.Flagged;
            return false;
        }

        value = existing.Value;
        return true;
    }

    /// <summary>Renders a value the way the envelope reports it.</summary>
    public static string Show(object? v) => Render(v);

    /// <summary>
    /// Applies one edit. Never throws for an ordinary miss — a missing path or
    /// a type clash is a RESULT, not an exception, because batch has to report
    /// all of them rather than stopping at the first.
    /// </summary>
    public EditResult Apply(Edit edit)
    {
        var to = edit.Value.ToString();

        if (!Resolve(edit.Path, out var parent, out var leaf, out var existing,
                     out var resolveError, out var resolveFailure))
            return new EditResult(edit.Path, null, to, false, resolveError, resolveFailure);

        if (existing.Value is KVObject)
            return new EditResult(edit.Path, null, to, false,
                $"'{leaf}' is a block or array; v1 sets scalars only",
                EditFailure.NotAScalar);

        var from = Render(existing.Value);

        // A flagged value carries a type prefix (resource_name:, subclass:,
        // panorama:). Refused by name rather than silently rewritten — none of
        // them is a scalar stat, and getting one wrong is invisible in a diff.
        if (existing.Flag != KVFlag.None)
            return new EditResult(edit.Path, from, to, false,
                $"'{leaf}' is a {existing.Flag} value; v1 sets plain scalars only",
                EditFailure.Flagged);

        if (!TryCoerce(existing, edit.Value, out var boxed, out var why))
            return new EditResult(edit.Path, from, to, false, why, EditFailure.TypeMismatch);

        // Reuse Type and Flag: only the boxed value changes.
        parent!.Properties[leaf] = new KVValue(existing.Type, existing.Flag, boxed!);
        return new EditResult(edit.Path, from, to, true, null);
    }

    /// <summary>
    /// The document's existing type wins. Writing a fractional value into a
    /// field that has always been an integer is how a vdata edit silently
    /// changes meaning, so a lossy conversion is refused rather than rounded.
    /// Dispatch is on the RUNTIME type of the existing value.
    /// </summary>
    private static bool TryCoerce(KVValue existing, ScalarValue wanted,
                                  out object? boxed, out string? error)
    {
        boxed = null;
        error = null;

        switch (existing.Value)
        {
            case bool:
                if (wanted.Kind != ScalarKind.Bool)
                {
                    error = $"field is a bool; got '{wanted.Raw}'";
                    return false;
                }
                boxed = (bool)wanted.Value;
                return true;

            case string:
                boxed = wanted.ToString();
                return true;

            case double or float:
                if (wanted.Kind is ScalarKind.Double or ScalarKind.Long)
                {
                    boxed = wanted.Kind == ScalarKind.Long
                        ? (double)(long)wanted.Value
                        : (double)wanted.Value;
                    return true;
                }
                error = $"field is a number; got '{wanted.Raw}'";
                return false;

            case sbyte or byte or short or ushort or int or uint or long or ulong:
                if (wanted.Kind == ScalarKind.Long)
                {
                    boxed = (long)wanted.Value;
                    return true;
                }
                if (wanted.Kind == ScalarKind.Double)
                {
                    var d = (double)wanted.Value;
                    if (Math.Abs(d % 1) > double.Epsilon)
                    {
                        error = $"field is an integer; '{wanted.Raw}' is fractional";
                        return false;
                    }
                    boxed = (long)d;
                    return true;
                }
                error = $"field is an integer; got '{wanted.Raw}'";
                return false;

            case null:
                error = "field is null; v1 will not assign a type to it";
                return false;

            default:
                error = $"field holds {existing.Value.GetType().Name}, " +
                        "which v1 does not support (scalars only)";
                return false;
        }
    }


    /// <summary>
    /// Every addressable scalar in the document, as (path, kind, value).
    ///
    /// Used by `diff`. Arrays are reported as a single opaque entry rather
    /// than descended into: their elements have no dotted path, so a change
    /// inside one cannot be named, and pretending otherwise would emit paths
    /// that dl then refuses. An array whose length changes shows up as
    /// a changed entry; an element edited in place does not. That is a stated
    /// limitation, not an oversight — v1 refuses array traversal everywhere.
    ///
    /// `kind` carries the KVFlag for flagged values (resource_name: and
    /// friends) so a diff can tell a genuine value change from a type change.
    /// </summary>
    public IEnumerable<(string Path, string Kind, string Value)> Flatten()
    {
        var root = _file.Root;
        if (root is null) yield break;
        foreach (var entry in Walk(root, ""))
            yield return entry;
    }

    private static IEnumerable<(string, string, string)> Walk(KVObject node, string prefix)
    {
        foreach (var kv in node.Properties)
        {
            var path = prefix.Length == 0 ? kv.Key : prefix + "." + kv.Key;
            var value = kv.Value;

            if (value.Value is KVObject child)
            {
                if (child.IsArray)
                {
                    yield return (path, "array", "[" + child.Properties.Count + " items]");
                    continue;
                }
                foreach (var entry in Walk(child, path))
                    yield return entry;
                continue;
            }

            var kind = value.Flag != KVFlag.None
                ? value.Flag.ToString()
                : (value.Value?.GetType().Name ?? "null");
            yield return (path, kind, Render(value.Value));
        }
    }

    /// <summary>
    /// Comparison form. Floats normalise to 6dp so VRF's own reformatting
    /// never registers as a difference — a diff that reported every float in
    /// the file after a no-op round trip would be useless.
    /// </summary>
    public static string Comparable(string kind, string value)
    {
        if (double.TryParse(value, NumberStyles.Float, CultureInfo.InvariantCulture, out var d))
            return d.ToString("F6", CultureInfo.InvariantCulture);
        return value;
    }

    private static string Render(object? v) => v switch
    {
        null => "null",
        bool b => b ? "true" : "false",
        double d => d.ToString("R", CultureInfo.InvariantCulture),
        float f => f.ToString("R", CultureInfo.InvariantCulture),
        IFormattable i => i.ToString(null, CultureInfo.InvariantCulture),
        _ => v.ToString() ?? "null"
    };
}
