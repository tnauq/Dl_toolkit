using System.Collections.Generic;
using System.Text;

namespace Deadlock.Format.Dmx;

/// <summary>
/// Writer for the keyvalues2 / keyvalues2_noids text encodings.
///
/// LAYOUT is copied from real dmxconvert output so emitted files diff cleanly
/// against it: tab indent, CRLF line endings, one attribute per line, arrays
/// on their own bracketed block with a trailing comma on every item except
/// the last, and empty arrays written as an open and close bracket on
/// consecutive lines.
///
/// BYTE-IDENTICAL OUTPUT IS NOT THE GOAL and must not become an assertion.
/// dmxconvert is free to order or format differently and still be correct.
/// The check that matters is the census after a round trip through the
/// binary encoding, where dmxconvert acts as an independent judge.
/// </summary>
public static class Kv2Writer
{
    private const string Nl = "\r\n";

    public static string Write(DmxDocument doc)
    {
        var sb = new StringBuilder();
        sb.Append("<!-- dmx encoding ").Append(doc.Encoding).Append(' ')
          .Append(doc.EncodingVersion).Append(" format ").Append(doc.Format)
          .Append(' ').Append(doc.FormatVersion).Append(" -->").Append(Nl);

        foreach (var root in doc.Roots)
        {
            WriteElement(sb, root, 0, root.TypeName);
        }
        return sb.ToString();
    }

    private static void Indent(StringBuilder sb, int depth)
        => sb.Append('\t', depth);

    private static void WriteElement(StringBuilder sb, DmxElement el, int depth, string label)
    {
        Indent(sb, depth); Q(sb, label); sb.Append(Nl);
        Indent(sb, depth); sb.Append('{').Append(Nl);

        foreach (var (name, value) in el.Attributes)
        {
            WriteAttribute(sb, name, value, depth + 1);
        }

        Indent(sb, depth); sb.Append('}').Append(Nl);
    }

    private static void WriteAttribute(StringBuilder sb, string name, DmxValue v, int depth)
    {
        switch (v.Kind)
        {
            case DmxValueKind.Scalar:
                Indent(sb, depth);
                Q(sb, name); sb.Append(' ');
                Q(sb, v.TypeName); sb.Append(' ');
                Q(sb, v.Scalar ?? string.Empty);
                sb.Append(Nl);
                return;

            case DmxValueKind.Inline:
                Indent(sb, depth);
                Q(sb, name); sb.Append(' ');
                Q(sb, v.TypeName); sb.Append(Nl);
                Indent(sb, depth); sb.Append('{').Append(Nl);
                foreach (var (n2, v2) in v.Element!.Attributes)
                    WriteAttribute(sb, n2, v2, depth + 1);
                Indent(sb, depth); sb.Append('}').Append(Nl);
                return;

            case DmxValueKind.Array:
                Indent(sb, depth);
                Q(sb, name); sb.Append(' ');
                Q(sb, v.TypeName); sb.Append(' ').Append(Nl);
                Indent(sb, depth); sb.Append('[').Append(Nl);
                WriteItems(sb, v.Items ?? new List<DmxItem>(), depth + 1);
                Indent(sb, depth); sb.Append(']').Append(Nl);
                return;
        }
    }

    private static void WriteItems(StringBuilder sb, IReadOnlyList<DmxItem> items, int depth)
    {
        for (var i = 0; i < items.Count; i++)
        {
            var last = i == items.Count - 1;
            var it = items[i];
            switch (it.Kind)
            {
                case DmxItemKind.Scalar:
                    Indent(sb, depth); Q(sb, it.Text ?? string.Empty);
                    if (!last) sb.Append(',');
                    sb.Append(Nl);
                    break;

                case DmxItemKind.Reference:
                    Indent(sb, depth);
                    Q(sb, "element"); sb.Append(' '); Q(sb, it.Text ?? string.Empty);
                    if (!last) sb.Append(',');
                    sb.Append(Nl);
                    break;

                case DmxItemKind.Inline:
                    var el = it.Element!;
                    Indent(sb, depth); Q(sb, el.TypeName); sb.Append(Nl);
                    Indent(sb, depth); sb.Append('{').Append(Nl);
                    foreach (var (n, v) in el.Attributes)
                        WriteAttribute(sb, n, v, depth + 1);
                    Indent(sb, depth); sb.Append('}');
                    if (!last) sb.Append(',');
                    sb.Append(Nl);
                    break;
            }
        }
    }

    private static void Q(StringBuilder sb, string s)
    {
        sb.Append('"');
        foreach (var c in s)
        {
            if (c == '"' || c == '\\') sb.Append('\\');
            sb.Append(c);
        }
        sb.Append('"');
    }
}
