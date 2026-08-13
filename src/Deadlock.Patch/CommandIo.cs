using Deadlock.Contracts;

namespace Deadlock.Patch;

/// <summary>
/// Tool identity, shared by every front end.
/// </summary>
internal static class Tool
{
    public const string Name = "dl";
    public const string Version = "0.2.0";
}

/// <summary>
/// Envelope emission, in ONE place.
///
/// ADDED 2026-08-13. Each of the four commands carried its own near-identical
/// Emit / Misuse / Fail trio — copied forward each time a mode was added, and
/// by the fourth the only differences were the payload type and the human
/// summary line. That is duplication with no upside: a change to the envelope
/// contract had four sites to remember, and one of them would eventually be
/// missed.
///
/// Split of responsibility:
///   - THIS type owns the envelope: tool identity, pinned build, ok/errors,
///     and the JSON-versus-stderr branch. Identical across every mode.
///   - Each COMMAND owns its human-readable summary, which genuinely differs —
///     "wrote N files", "N differences", "packed N entries" — and passes it as
///     a callback.
///
/// stdout is a machine interface (D5). Under --json, the envelope is the ONLY
/// thing written there; every diagnostic goes to stderr.
/// </summary>
internal static class CommandIo
{
    /// <summary>
    /// Emit an envelope and return the exit code.
    /// </summary>
    /// <param name="data">The payload. Never null; use an empty instance.</param>
    /// <param name="error">Null on success.</param>
    /// <param name="exitCode">Returned unchanged, so callers read as one line.</param>
    /// <param name="json">Envelope to stdout when true.</param>
    /// <param name="pinnedBuild">Build id, where the mode requires one (D2).</param>
    /// <param name="body">
    /// Per-item lines, written to stderr BEFORE the error block — preserving
    /// the ordering every command already had: what happened, then why it
    /// failed, then the closing summary.
    /// </param>
    /// <param name="footer">
    /// Closing summary, written AFTER the error block. Commands typically skip
    /// their success summary when an error is present.
    /// </param>
    public static int Emit<T>(
        T data,
        ToolError? error,
        int exitCode,
        bool json,
        string? pinnedBuild = null,
        Action? body = null,
        Action? footer = null)
    {
        var envelope = new Envelope<T>
        {
            Tool = Tool.Name,
            Version = Tool.Version,
            PinnedBuild = pinnedBuild,
            Ok = error is null,
            Data = data
        };
        if (error is not null) envelope.Errors.Add(error);

        if (json)
        {
            Json.ToStdout(envelope);
            return exitCode;
        }

        body?.Invoke();

        if (error is not null)
        {
            Console.Error.WriteLine($"error: {error.Message}");
            Console.Error.WriteLine($"  fix: {error.Fix}");
        }

        footer?.Invoke();
        return exitCode;
    }

    /// <summary>
    /// Argument misuse. Always exit 2, always prints usage to stderr.
    ///
    /// The payload is empty by construction: misuse means the tool never got
    /// far enough to have a result, and inventing a half-populated one would
    /// make `data` mean two different things.
    /// </summary>
    public static int Misuse<T>(string message, bool json, string usage, string helpHint)
        where T : new()
        => Emit(
            new T(),
            new ToolError(ErrorCode.Misuse, message, helpHint),
            Exit.Misuse,
            json,
            footer: () =>
            {
                Console.Error.WriteLine();
                Console.Error.WriteLine(usage);
            });

    /// <summary>
    /// A named failure with a populated payload where one exists.
    /// </summary>
    public static int Fail<T>(
        T data, string code, string message, string fix, int exitCode, bool json,
        string? pinnedBuild = null, Action? body = null, Action? footer = null)
        => Emit(data, new ToolError(code, message, fix), exitCode, json,
                pinnedBuild, body, footer);
}
