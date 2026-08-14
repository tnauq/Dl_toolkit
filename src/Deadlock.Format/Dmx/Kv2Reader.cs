using System;
using System.Collections.Generic;
using System.Text;
using System.Text.RegularExpressions;

namespace Deadlock.Format.Dmx;

/// <summary>
/// Reader for DMX in the keyvalues2 and keyvalues2_noids text encodings.
///
/// GRAMMAR, validated against dl_example.vmap converted by dmxconvert
/// (2026-08-14) before this file was written:
///
///   header      := "&lt;!-- dmx encoding &lt;enc&gt; &lt;n&gt; format &lt;fmt&gt; &lt;n&gt; --&gt;"
///   document    := header element*
///   element     := STRING "{" attribute* "}"
///   attribute   := STRING STRING value
///   value       := STRING                 (scalar)
///                | "{" ... "}"            (inline contained element)
///                | "[" item ("," item)* "]"
///   item        := STRING                 (scalar, or an element TYPE NAME)
///                | STRING STRING          ("element" "&lt;guid&gt;" reference)
///                | STRING "{" ... "}"     (inline element inside an array)
///
/// TWO THINGS THAT LOOK ALIKE AND ARE NOT:
///
/// 1. After "key" "type", the NEXT TOKEN decides everything. '{' means a
///    contained element whose type name is the second string; '[' means an
///    array; a string means a scalar. Do not branch on the type name.
/// 2. Inside an element_array, an item may be either an "element" "&lt;guid&gt;"
///    PAIR or an inline "TypeName" { ... } BLOCK. Both open with a string,
///    so again the following token decides.
///
/// Binary attributes are ordinary quoted strings that happen to span many
/// lines of hex. They need no special case.
///
/// NOTE ON IDS: keyvalues2_noids omits "id" "elementid" for elements that are
/// referenced only once, and keeps it where an element is genuinely shared
/// (measured: 767 ids for 768 multiply-referenced elements in the fixture).
/// This reader does not care either way; an absent id is simply an absent
/// attribute.
/// </summary>
public static class Kv2Reader
{
    private static readonly Regex HeaderRx = new(
        @"<!--\s*dmx encoding (\S+) (\d+) format (\S+) (\d+)\s*-->",
        RegexOptions.Compiled);

    private enum T { Str, LBrace, RBrace, LBracket, RBracket, Comma, Eof }

    public static DmxReadResult Read(string text)
    {
        var head = text.Length > 256 ? text.Substring(0, 256) : text;
        var m = HeaderRx.Match(head);
        if (!m.Success) return DmxReadResult.Fail(DmxFailure.MissingHeader, 0);

        var enc = m.Groups[1].Value;
        if (!enc.StartsWith("keyvalues2", StringComparison.Ordinal))
            return DmxReadResult.Fail(DmxFailure.UnsupportedEncoding, m.Index);

        var doc = new DmxDocument(
            enc,
            int.Parse(m.Groups[2].Value),
            m.Groups[3].Value,
            int.Parse(m.Groups[4].Value));

        var p = new P(text, m.Index + m.Length);
        try
        {
            p.Next();
            while (p.Kind != T.Eof)
            {
                var typeName = p.TakeString();
                doc.Roots.Add(p.ParseElement(typeName));
            }
        }
        catch (ParseError e)
        {
            return DmxReadResult.Fail(e.Failure, e.Offset);
        }

        return DmxReadResult.Success(doc);
    }

    private sealed class ParseError : Exception
    {
        public ParseError(DmxFailure f, int offset) { Failure = f; Offset = offset; }
        public DmxFailure Failure { get; }
        public int Offset { get; }
    }

    private sealed class P
    {
        private readonly string _s;
        private int _i;

        public P(string s, int start) { _s = s; _i = start; }

        public T Kind { get; private set; }
        public string Text { get; private set; } = string.Empty;
        public int Pos { get; private set; }

        public void Next()
        {
            while (_i < _s.Length)
            {
                var c = _s[_i];
                if (c is ' ' or '\t' or '\r' or '\n') { _i++; continue; }
                if (c == '/' && _i + 1 < _s.Length && _s[_i + 1] == '/')
                {
                    var nl = _s.IndexOf('\n', _i);
                    _i = nl < 0 ? _s.Length : nl + 1;
                    continue;
                }
                break;
            }

            Pos = _i;
            if (_i >= _s.Length) { Kind = T.Eof; Text = string.Empty; return; }

            var ch = _s[_i];
            switch (ch)
            {
                case '{': Kind = T.LBrace; _i++; return;
                case '}': Kind = T.RBrace; _i++; return;
                case '[': Kind = T.LBracket; _i++; return;
                case ']': Kind = T.RBracket; _i++; return;
                case ',': Kind = T.Comma; _i++; return;
                case '"': ReadString(); return;
                default: throw new ParseError(DmxFailure.UnexpectedCharacter, _i);
            }
        }

        private void ReadString()
        {
            var sb = new StringBuilder();
            var j = _i + 1;
            while (j < _s.Length)
            {
                var c = _s[j];
                if (c == '\\' && j + 1 < _s.Length) { sb.Append(_s[j + 1]); j += 2; continue; }
                if (c == '"') { Kind = T.Str; Text = sb.ToString(); _i = j + 1; return; }
                sb.Append(c); j++;
            }
            throw new ParseError(DmxFailure.UnterminatedString, _i);
        }

        public string TakeString()
        {
            if (Kind != T.Str) throw new ParseError(DmxFailure.UnexpectedToken, Pos);
            var v = Text; Next(); return v;
        }

        public void Expect(T k)
        {
            if (Kind != k)
            {
                throw new ParseError(
                    Kind == T.Eof ? DmxFailure.TruncatedInput : DmxFailure.UnexpectedToken,
                    Pos);
            }
            Next();
        }

        public DmxElement ParseElement(string typeName)
        {
            var el = new DmxElement(typeName);
            Expect(T.LBrace);
            while (Kind != T.RBrace)
            {
                if (Kind == T.Eof) throw new ParseError(DmxFailure.TruncatedInput, Pos);
                var key = TakeString();
                var vtype = TakeString();
                el.Set(key, ParseValue(vtype));
            }
            Expect(T.RBrace);
            return el;
        }

        private DmxValue ParseValue(string vtype)
        {
            switch (Kind)
            {
                case T.LBrace:
                    return DmxValue.OfInline(vtype, ParseElement(vtype));
                case T.LBracket:
                    return DmxValue.OfArray(vtype, ParseArray(vtype));
                case T.Str:
                    return DmxValue.OfScalar(vtype, TakeString());
                case T.Eof:
                    throw new ParseError(DmxFailure.TruncatedInput, Pos);
                default:
                    throw new ParseError(DmxFailure.UnexpectedToken, Pos);
            }
        }

        private List<DmxItem> ParseArray(string vtype)
        {
            var isElementArray = vtype.Equals("element_array", StringComparison.Ordinal);
            var items = new List<DmxItem>();
            Expect(T.LBracket);
            while (Kind != T.RBracket)
            {
                if (Kind == T.Eof) throw new ParseError(DmxFailure.TruncatedInput, Pos);
                if (Kind == T.Comma) { Next(); continue; }
                if (Kind != T.Str) throw new ParseError(DmxFailure.UnexpectedToken, Pos);

                var first = TakeString();
                if (Kind == T.LBrace)
                {
                    items.Add(DmxItem.Inline(ParseElement(first)));
                }
                else if (isElementArray && Kind == T.Str)
                {
                    items.Add(DmxItem.Reference(TakeString()));
                }
                else
                {
                    items.Add(DmxItem.Scalar(first));
                }
            }
            Expect(T.RBracket);
            return items;
        }
    }
}
