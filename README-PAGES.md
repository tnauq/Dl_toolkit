# Publishing the viewer on GitHub Pages

Everything below is doable from the GitHub web UI on a phone. No Actions
workflow, no build step, no local git.

## What is in this drop

    docs/index.html            the viewer
    docs/plans/index.json      the menu manifest
    docs/plans/sealed_room.json
    docs/plans/two_lane.json   a bigger test layout

**Why `docs/` and not the repo root.** GitHub Pages can serve from a
`/docs` folder on `main` with no workflow at all, which is the fewest
moving parts. It also means the site publishes ONLY what is in `docs/` —
your 15 MB `dl_example.vmap` at the repo root stays out of the published
site. That matters: the repo is public, and Pages would otherwise serve
it to anyone.

## Setup, once

1. **Unzip this at the repo root and run `inbox`.** You should end up with
   a `docs/` folder containing the four files above.
2. In the repo on GitHub, open **Settings** (gear icon, or the `...` menu
   on mobile).
3. Scroll to **Pages** in the left sidebar.
4. Under **Build and deployment**:
   - **Source**: `Deploy from a branch`
   - **Branch**: `main`
   - **Folder**: `/docs`
   - Tap **Save**.
5. Wait roughly one to two minutes. The Pages panel will show the live
   URL, which will be:

       https://tnauq.github.io/Dl_toolkit/

6. Open it. You should get the sealed room, with a map menu at the
   bottom left.

If you get a 404 for a minute or two, that is normal on first deploy.
If it persists, check the **Actions** tab: Pages runs a `pages-build-
deployment` job and its log says what it did not like.

## Adding a map later

Two steps, both in the web UI:

1. **Add the plan.** Go to `docs/plans/`, tap **Add file** ->
   **Create new file**, name it `whatever.json`, paste the plan, commit.
2. **List it in the menu.** Open `docs/plans/index.json`, tap the pencil,
   add one line:

   ```json
   {
     "plans": [
       { "name": "Sealed room",   "file": "sealed_room.json" },
       { "name": "Two lane test", "file": "two_lane.json" },
       { "name": "My new map",    "file": "whatever.json" }
     ]
   }
   ```

   `name` is what shows in the menu. `file` is the filename inside
   `plans/`. Commit, wait a minute, reload.

**The manifest is deliberately manual.** A static site cannot list a
directory, so something has to enumerate the plans. One line per map in a
file you are already editing beats generating an index in CI.

## Switching maps

- **The menu**, bottom left. Picking a map updates the URL, so the link
  in your address bar is always shareable.
- **Direct link**: `?plan=plans/two_lane.json` appended to the page URL.
  Handy for sending someone a specific layout.
- **Open file**, for a plan that is not published. Works on the live site
  and is the only route that works when you open `index.html` straight
  off disk, since a `file://` page cannot fetch.

Paths are relative on purpose. Pages serves this repo under the
`/Dl_toolkit/` subpath, and any absolute path (a leading `/`) would break
there. The viewer rejects absolute and cross-origin `?plan=` values
rather than failing confusingly.

## Full screen

- **iPhone Safari does not support the Fullscreen API**, so the button
  hides itself there rather than doing nothing. The real route is
  **Share -> Add to Home Screen**. The viewer carries the standalone
  meta tags, so launching from the home screen icon has no browser
  chrome at all. That is the best fullscreen available on iOS, and it is
  better than the button anyway.
- On desktop and Android the **full screen** button does a real
  fullscreen request.

## Controls

- **D-pad**, bottom right. Eight-way from a single thumb: direction comes
  from the angle of your touch, snapped to 45 degrees.
- **Drag anywhere else** to look.
- **WASD / arrows** and mouse drag on desktop. `Q`/`E` for down and up
  while noclip is on.
- **respawn** returns you to the first entity in the plan.

## Keeping it in sync with the emitter

`docs/plans/*.json` and `examples/*.mapplan.json` are the same format. If
a plan is one you actually intend to emit, keep the canonical copy in
`examples/` and copy it into `docs/plans/` for viewing, rather than
letting the two drift. Nothing enforces this yet; a CI step that copies
`examples/` into `docs/plans/` and rewrites the manifest would, if the
duplication starts to bite.

## Note on the two_lane plan

It exists to exercise the viewer with something more than a box: a
divider down the middle, two cover blocks, and a ledge with a step up to
it, so step height, sliding along walls and the depth sort all get a
workout. Its spawns were checked programmatically to sit on a floor and
not inside a solid — the first version had a trooper spawn buried inside
the ledge, which looked perfectly fine as JSON.
