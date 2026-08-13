---
name: mabl-dom-sanitizer
description: Strip executable JavaScript from a captured mabl DOM snapshot so it can be opened locally without the app forcing a logout. Use this skill whenever someone wants to clean, sanitize, or "de-JS" a mabl DOM snapshot, saved HTML page, or DOMSnapshot.html; or reports that opening a saved mabl page kicks them out, redirects to login, re-hydrates the SPA, or won't load statically. Also triggers on phrases like "remove the javascript from this snapshot", "make this saved mabl page loadable", "the snapshot logs me out when I open it", "prep a DOM snapshot", "static-ify this mabl page", or any request to open/inspect a captured mabl HTML page offline. Tuned for mabl snapshots (gatethree.com / cdn.gatethree.com bundles) but works on any DOM snapshot.
---

# mabl DOM Snapshot Sanitizer

## Why this exists

A DOM snapshot captured from the mabl app is a full HTML dump of a rendered page.
When you open that file directly in a browser, the page's own JavaScript runs
again: the SPA re-hydrates, a session/auth check fails (there's no live session
behind a saved file), and the app **forces a logout** or bounces you to the login
screen before you can inspect anything.

The fix is to remove every way the page can execute JavaScript, while keeping the
DOM, styles, and rendered content exactly as they were. The result is a static,
inert copy you can open and inspect offline without being kicked out.

## What to do

Run the bundled script against the snapshot. It does the whole transformation and
prints a report of what it removed and a verification that no script tags remain.

```bash
python3 scripts/sanitize_dom_snapshot.py "<path to snapshot>.html"
```

By default it writes `<name>.sanitized.html` next to the input. To choose the
output path (for example, to write straight into the user's folder), pass `-o`:

```bash
python3 scripts/sanitize_dom_snapshot.py "DOMSnapshot.html" -o "DOMSnapshot.clean.html"
```

The script is pure Python 3 standard library — no dependencies to install.

## What it removes vs. preserves

It strips every executable-JS vector:

- `<script>` blocks — both external bundles (`src=`, e.g. the mabl app's
  runtime/main/reactVendor chunks from `gatethree.com`) and inline scripts
- inline event handlers (`onclick`, `onload`, `onerror`, any `on...=`)
- `javascript:` URLs in `href` / `src` / `action` attributes (blanked, attribute kept)
- `<meta http-equiv="refresh">` auto-redirects
- `<link rel="preload|modulepreload" as="script">` script preloads

It leaves everything visual intact: the full DOM and text content, inline
`style=""` attributes and CSS custom properties, `<style>` blocks, stylesheet
`<link>`s, images, and SVGs. That's why the page still renders correctly — only
the behavior that would trigger the logout is gone.

## Verify the result

The script already reports a count of removed items and confirms
`0 script tags remain`. If you want an independent check, or the user asks you to
confirm, grep the output:

```bash
grep -c "<script" "<output>.sanitized.html"   # expect 0
```

Then hand the sanitized file to the user (in Cowork, present it so they get a
clickable card). It's ready to open locally.

## Notes and edge cases

- The event-handler match is deliberately guarded so it won't corrupt attributes
  that merely start with the letters "on" (like `contenteditable` or `controls`).
- If the script reports "nothing to remove," the snapshot had no executable JS —
  it's already safe to open, and the logout was likely caused by something else
  (e.g. a stale service worker in the browser rather than the file itself).
- The transformation is generic, so it also works for non-mabl DOM snapshots; the
  mabl specifics above are just the common case this was built for.
