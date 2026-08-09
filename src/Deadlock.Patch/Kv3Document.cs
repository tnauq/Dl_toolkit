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
///
/// Design consequence worth stating: we never construct a KVValueType, we
/// REUSE the existing one along with its Flag. That preserves typed prefixes
/// such as resource_name: for free, and means this file names no enum member
/// it has not verified. Classification is done on the runtime type of
/// .Value — bool, long, double, string — which the dump confirms directly.
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

    /// <summary>
    /// Applies one edit. Never throws for an ordinary miss — a missing path or
    /// a type clash is a RESULT, not an exception, because batch has to report
    /// all of them rather than stopping at the first.
    /// </summary>
    public EditResult Apply(Edit edit)
    {
        var segments = edit.Path.Split('.');
        var to = edit.Value.ToString();

        var node = _file.Root;
        if (node is null)
            return new EditResult(edit.Path, null, to, false, "document has no root object");

        for (var i = 0; i < segments.Length - 1; i++)
        {
            var seg = segments[i];
            if (!node.Properties.TryGetValue(seg, out var childValue))
                return new EditResult(edit.Path, null, to, false,
                    $"path not found: no key '{seg}' at '{string.Join('.', segments[..(i + 1)])}'");

            if (childValue.Value is not KVObject childObj)
                return new EditResult(edit.Path, null, to, false,
                    $"path traverses a scalar: '{seg}' is a value, not a block");

            if (childObj.IsArray)
                return new EditResult(edit.Path, null, to, false,
                    $"'{seg}' is an array; v1 does not address array elements");

            node = childObj;
        }

        var leaf = segments[^1];
        if (!node.Properties.TryGetValue(leaf, out var existing))
            return new EditResult(edit.Path, null, to, false,
                $"path not found: no key '{leaf}'");

        if (existing.Value is KVObject)
            return new EditResult(edit.Path, null, to, false,
                $"'{leaf}' is a block or array; v1 sets scalars only");

        var from = Render(existing.Value);

        // A flagged value carries a type prefix (resource_name:, subclass:,
        // panorama:). Refused by name rather than silently rewritten — none of
        // them is a scalar stat, and getting one wrong is invisible in a diff.
        if (existing.Flag != KVFlag.None)
            return new EditResult(edit.Path, from, to, false,
                $"'{leaf}' is a {existing.Flag} value; v1 sets plain scalars only");

        if (!TryCoerce(existing, edit.Value, out var boxed, out var why))
            return new EditResult(edit.Path, from, to, false, why);

        // Reuse Type and Flag: only the boxed value changes.
        node.Properties[leaf] = new KVValue(existing.Type, existing.Flag, boxed!);
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
