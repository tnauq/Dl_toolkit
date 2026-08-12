namespace Deadlock.Patch;

/// <summary>
/// Argv dispatch and nothing else.
///
/// Subcommands are used rather than flags because the modes take
/// disjoint arguments — sharing one parser would mean validating that --plan
/// and --set are never both present, which is a rule the shape can express for
/// free instead.
///
/// The default mode is unchanged and takes NO subcommand, so every existing
/// invocation and every patch-smoke assertion keeps working:
///
///   dl-patch --in a.vdata --out b.vdata --set x.y=1
///   dl-patch batch --plan p.json --root . --out-root out --source-build &lt;sha&gt;
///   dl-patch diff --old a.vdata --new b.vdata
///   dl-patch pack --in game/citadel --out pak01_dir.vpk --source-build &lt;sha&gt;
/// </summary>
internal static class Program
{
    private static int Main(string[] args)
    {
        if (args.Length > 0 && args[0] == "batch") return BatchCommand.Run(args[1..]);
        if (args.Length > 0 && args[0] == "diff") return DiffCommand.Run(args[1..]);
        if (args.Length > 0 && args[0] == "pack") return PackCommand.Run(args[1..]);
        return SetCommand.Run(args);
    }
}
