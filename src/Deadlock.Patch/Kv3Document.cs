using System.Globalization;
using ValveResourceFormat.Serialization.KeyValues;

namespace Deadlock.Patch;

/// <summary>
/// Wraps VRF's KV3 object model. THE ONLY FILE THAT TOUCHES IT — if VRF's API
/// differs from what is written here, this is the single file to fix.
///
/// Confidence: the round trip (load -> save) is [V-CI], proven by probe-kv3
/// 2026-08-09 on a 2.1 MB CitadelHeroData_t file — 63,490 keys in and out,
/// typed prefixes preserved, no precision at risk.
///
/// MUTATION IS [?]. The probe never set a value. KVObject's property setter
/// and KVValue's constructor are written from expectation, not from reading
/// the source. patch-smoke exists to convert that [?] into [V-CI] or into a
/// one-file fix.
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

        if (_file.Root is not KVObject root)
            return new EditResult(edit.Path, null, edit.Value.ToString(), false,
                "document root is not an object");

        var node = root;
        for (var i = 0; i < segments.Length - 1; i++)
        {
            var seg = segments[i];
            if (!TryGetChild(node, seg, out var child))
                return new EditResult(edit.Path, null, edit.Value.ToString(), false,
                    $"path not found: no key '{seg}' at '{string.Join('.', segments[..(i + 1)])}'");

            if (child is not KVObject childObj)
                return new EditResult(edit.Path, null, edit.Value.ToString(), false,
                    $"path traverses a scalar: '{seg}' is a value, not an object");

            node = childObj;
        }

        var leaf = segments[^1];
        if (!TryGetChild(node, leaf, out var existing))
            return new EditResult(edit.Path, null, edit.Value.ToString(), false,
                $"path not found: no key '{leaf}'");

        if (existing is KVObject)
            return new EditResult(edit.Path, null, edit.Value.ToString(), false,
                $"'{leaf}' is an object; v1 sets scalars only");

        var existingValue = node.Properties[leaf];
        var from = Render(existing);

        if (!TryCoerce(existingValue, edit.Value, out var newValue, out var why))
            return new EditResult(edit.Path, from, edit.Value.ToString(), false, why);

        node.Properties[leaf] = newValue!;
        return new EditResult(edit.Path, from, edit.Value.ToString(), true, null);
    }

    private static bool TryGetChild(KVObject node, string key, out object? value)
    {
        value = null;
        if (!node.Properties.ContainsKey(key)) return false;
        value = node.Properties[key].Value;
        return true;
    }

    /// <summary>
    /// The document's existing type wins. Writing a double into a field that
    /// has always been an integer is how a vdata edit silently changes meaning,
    /// so a lossy conversion is refused rather than rounded.
    /// </summary>
    private static bool TryCoerce(KVValue existing, ScalarValue wanted,
                                  out KVValue? result, out string? error)
    {
        result = null;
        error = null;

        switch (existing.Type)
        {
            case KVType.BOOLEAN:
                if (wanted.Kind != ScalarKind.Bool)
                {
                    error = $"field is a bool; got '{wanted.Raw}'";
                    return false;
                }
                result = new KVValue(KVType.BOOLEAN, (bool)wanted.Value);
                return true;

            case KVType.INT64:
            case KVType.UINT64:
                if (wanted.Kind == ScalarKind.Long)
                {
                    result = new KVValue(existing.Type, (long)wanted.Value);
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
                    result = new KVValue(existing.Type, (long)d);
                    return true;
                }
                error = $"field is an integer; got '{wanted.Raw}'";
                return false;

            case KVType.DOUBLE:
                if (wanted.Kind is ScalarKind.Double or ScalarKind.Long)
                {
                    var d = wanted.Kind == ScalarKind.Long
                        ? (double)(long)wanted.Value
                        : (double)wanted.Value;
                    result = new KVValue(KVType.DOUBLE, d);
                    return true;
                }
                error = $"field is a number; got '{wanted.Raw}'";
                return false;

            case KVType.STRING:
                result = new KVValue(KVType.STRING, wanted.ToString());
                return true;

            default:
                // resource_name:, subclass: and friends. Refused on purpose:
                // they carry a type prefix that a naive string write would drop,
                // and nothing in v1 needs them.
                error = $"field type {existing.Type} is not supported by v1 (scalars only)";
                return false;
        }
    }

    private static string Render(object? v) => v switch
    {
        null => "null",
        bool b => b ? "true" : "false",
        double d => d.ToString("R", CultureInfo.InvariantCulture),
        IFormattable f => f.ToString(null, CultureInfo.InvariantCulture),
        _ => v.ToString() ?? "null"
    };
}
