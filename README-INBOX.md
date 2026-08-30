# Inbox drop — HANDOFF_20260830 (2026-08-30)

    HANDOFF_20260830.md    NEW

Additive, one file. `HANDOFF_20260829.md` is left in place - its reasoning is
worth keeping even where its conclusions were overturned - but the new one
opens by saying it is superseded.

Covers: the three FGD files arriving, the connection probe and its two
failed runs, guardians becoming spawn markers, the proxy going off and back
on, the lid becoming an entity, the gated midboss chain, cover groups,
reinforcement spawns, and the re-pinned counts.

Two things in it are worth reading even if you were here for the session:

**§7 warns not to "fix" `EXPECT_MAPMESH`.** It stayed at 4779 while
`EXPECT_BOXES` fell to 4745, because the lid's mesh moved from a box to an
entity. Mesh count is no longer boxes + n, and that looks like a bug to
anyone who does not know why.

**The FGD trust rule, at the top.** Presences are strong evidence, absences
are weak, and the fixture outranks the FGD when they disagree - which
happened twice this session and the shipped map won both times.
