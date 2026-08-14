using System;
using System.Collections.Generic;

namespace Deadlock.Format.Dmx;

/// <summary>
/// Failure kinds are VALUES, never message text. Matches the EditFailure
/// convention in Deadlock.Contracts.
/// </summary>
public enum DmxFailure
{
    None = 0,
    MissingHeader,
    UnterminatedString,
    UnexpectedCharacter,
    UnexpectedToken,
    TruncatedInput,
    UnsupportedEncoding,
}

public enum DmxValueKind
{
    /// <summary>"key" "type" "value"</summary>
    Scalar,
    /// <summary>"key" "TypeName" { ... } — a contained child element.</summary>
    Inline,
    /// <summary>"key" "type_array" [ ... ]</summary>
    Array,
}

public enum DmxItemKind
{
    /// <summary>A plain value inside an array: "0", "1.5", ...</summary>
    Scalar,
    /// <summary>"element" "&lt;guid&gt;" inside an element_array.</summary>
    Reference,
    /// <summary>"TypeName" { ... } inline inside an element_array.</summary>
    Inline,
}

public sealed class DmxItem
{
    public DmxItemKind Kind { get; }
    public string? Text { get; }
    public DmxElement? Element { get; }

    private DmxItem(DmxItemKind kind, string? text, DmxElement? element)
    {
        Kind = kind; Text = text; Element = element;
    }

    public static DmxItem Scalar(string text) => new(DmxItemKind.Scalar, text, null);
    public static DmxItem Reference(string guid) => new(DmxItemKind.Reference, guid, null);
    public static DmxItem Inline(DmxElement el) => new(DmxItemKind.Inline, null, el);
}

public sealed class DmxValue
{
    public DmxValueKind Kind { get; }

    /// <summary>
    /// The declared type token as it appears in the file: "int", "float",
    /// "element_array", or an element type name such as "CDmePolygonMesh".
    /// </summary>
    public string TypeName { get; }

    public string? Scalar { get; }
    public DmxElement? Element { get; }
    public IReadOnlyList<DmxItem>? Items { get; }

    private DmxValue(DmxValueKind kind, string typeName, string? scalar,
                     DmxElement? element, IReadOnlyList<DmxItem>? items)
    {
        Kind = kind; TypeName = typeName; Scalar = scalar;
        Element = element; Items = items;
    }

    public static DmxValue OfScalar(string typeName, string text)
        => new(DmxValueKind.Scalar, typeName, text, null, null);

    public static DmxValue OfInline(string typeName, DmxElement el)
        => new(DmxValueKind.Inline, typeName, null, el, null);

    public static DmxValue OfArray(string typeName, IReadOnlyList<DmxItem> items)
        => new(DmxValueKind.Array, typeName, null, null, items);

    public bool IsArray => Kind == DmxValueKind.Array;
}

/// <summary>
/// One DMX element. Attribute ORDER is preserved: it is not semantically
/// load-bearing, but keeping it makes emitted files diffable against
/// dmxconvert output, which is the whole reason for using the text encoding.
/// </summary>
public sealed class DmxElement
{
    private readonly List<KeyValuePair<string, DmxValue>> _ordered = new();
    private readonly Dictionary<string, int> _index =
        new(StringComparer.Ordinal);

    public DmxElement(string typeName) => TypeName = typeName;

    public string TypeName { get; }

    public IReadOnlyList<KeyValuePair<string, DmxValue>> Attributes => _ordered;

    public void Set(string name, DmxValue value)
    {
        if (_index.TryGetValue(name, out var at))
        {
            _ordered[at] = new(name, value);
            return;
        }
        _index[name] = _ordered.Count;
        _ordered.Add(new(name, value));
    }

    public DmxValue? Get(string name)
        => _index.TryGetValue(name, out var at) ? _ordered[at].Value : null;

    public string? GetScalar(string name)
    {
        var v = Get(name);
        return v is { Kind: DmxValueKind.Scalar } ? v.Scalar : null;
    }

    /// <summary>Depth-first walk over this element and every contained one.</summary>
    public IEnumerable<DmxElement> Descend()
    {
        yield return this;
        foreach (var (_, v) in _ordered)
        {
            if (v.Kind == DmxValueKind.Inline && v.Element is not null)
            {
                foreach (var e in v.Element.Descend()) yield return e;
            }
            else if (v.Kind == DmxValueKind.Array && v.Items is not null)
            {
                foreach (var it in v.Items)
                {
                    if (it.Kind == DmxItemKind.Inline && it.Element is not null)
                    {
                        foreach (var e in it.Element.Descend()) yield return e;
                    }
                }
            }
        }
    }
}

public sealed class DmxDocument
{
    public DmxDocument(string encoding, int encodingVersion,
                       string format, int formatVersion)
    {
        Encoding = encoding; EncodingVersion = encodingVersion;
        Format = format; FormatVersion = formatVersion;
    }

    public string Encoding { get; }
    public int EncodingVersion { get; }
    public string Format { get; }
    public int FormatVersion { get; }

    public List<DmxElement> Roots { get; } = new();

    /// <summary>
    /// Every element in the document, including contained ones. This is what
    /// the census assertions count.
    /// </summary>
    public IEnumerable<DmxElement> AllElements()
    {
        foreach (var r in Roots)
            foreach (var e in r.Descend())
                yield return e;
    }
}

public readonly struct DmxReadResult
{
    public DmxReadResult(DmxFailure failure, int offset, DmxDocument? document)
    {
        Failure = failure; Offset = offset; Document = document;
    }

    public DmxFailure Failure { get; }

    /// <summary>Character offset of the failure, or the end of input.</summary>
    public int Offset { get; }

    public DmxDocument? Document { get; }

    public bool Ok => Failure == DmxFailure.None && Document is not null;

    public static DmxReadResult Success(DmxDocument doc)
        => new(DmxFailure.None, 0, doc);

    public static DmxReadResult Fail(DmxFailure f, int offset)
        => new(f, offset, null);
}
