# Inbox drop — the three FGDs, again, plus a louder validator (2026-08-30)

    docs/reference/citadel/citadel.fgd         (re-shipped)
    docs/reference/citadel/base.fgd            (re-shipped)
    docs/reference/citadel/postprocessing.fgd  (re-shipped)
    tools/fgd_check.py                         MODIFIED

`fgd_check` found no tables, which means one or both of the 2026-08-29 drops
carrying the FGDs never landed — `citadel.fgd` came in the `-fgd` drop,
`base.fgd` and `postprocessing.fgd` in the `-probefix` one. All three are
re-shipped here so it does not matter which was missed. They are byte
identical to what was sent before; if they are already committed this
overwrites them with themselves.

## The tool was too quiet about it, and that is the real bug

It printed `(missing, skipped)` per file and then a single error. In a long
log that reads like a clean run. **A validator that checks nothing and
reports nothing is indistinguishable from a validator that passes**, which is
how a check becomes decoration.

Three changes:

- **It searches** — `docs/reference/citadel`, `docs/reference`, `reference`,
  the repo root, and anything in `FGD_DIR`. It also picks up any other
  `.fgd` it finds, so a file we did not anticipate still counts.
- **Empty tables are a hard failure**, with the directories it looked in
  printed and a pointer to which drop carries which file.
- **A partial set warns**: if `base.fgd` is present but `citadel.fgd` is not,
  it says so, because classes defined only in the missing file will warn and
  those warnings would otherwise look like real findings.

`FGD_DIR` in the environment overrides the search, which is also the way to
point it at a working copy without committing anything.
