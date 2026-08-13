#!/usr/bin/env python3
"""
Sanitize a mabl DOM snapshot so it can be opened locally without the app's
JavaScript running (which otherwise re-hydrates the SPA, fails an auth/session
check, and forces a logout).

The script strips every executable-JavaScript vector from a captured HTML file
while leaving the DOM structure, inline styles, CSS, and rendered content
untouched. It's tuned for mabl snapshots (the app loads bundles from
gatethree.com / cdn.gatethree.com plus React/vendor chunks), but the removal is
generic and safe for any DOM snapshot.

What it removes:
  - <script> blocks (both external `src=` bundles and inline scripts)
  - inline event handlers (onclick, onload, onerror, on...=)
  - javascript: URLs in href/src/action attributes
  - <meta http-equiv="refresh"> auto-redirects
  - <link rel="preload|modulepreload" as="script"> script preloads

What it preserves:
  - the full DOM, text content, inline style="" attributes and CSS variables
  - <style> blocks and stylesheet <link>s
  - images, SVGs, and other non-executable resources

Usage:
    python3 sanitize_dom_snapshot.py INPUT.html [-o OUTPUT.html]

If -o is omitted, the output is written next to the input as
"<name>.sanitized.html". A short report of what was removed is printed to stderr.
"""

import argparse
import re
import sys
from pathlib import Path

# Pattern definitions. re.I = case-insensitive, re.S = dot matches newlines.
SCRIPT_BLOCK = re.compile(r"<script\b[^>]*>.*?</script>", re.I | re.S)
SCRIPT_SELF_CLOSING = re.compile(r"<script\b[^>]*/>", re.I)
# Inline event handlers: on<word>="..." / '...' / bare. Guard the left side with
# a whitespace/quote boundary so we don't match substrings like "contenteditable"
# (…"content"…) or "controls".
EVENT_HANDLER = re.compile(
    r"""(?<=[\s"'])on[a-z]+\s*=\s*(?:"[^"]*"|'[^']*'|[^\s>]+)""", re.I
)
JS_URL_ATTR = re.compile(
    r"""\b(href|src|action|formaction)\s*=\s*(["'])\s*javascript:[^"']*\2""", re.I
)
META_REFRESH = re.compile(
    r"""<meta\b[^>]*http-equiv\s*=\s*["']?refresh["']?[^>]*>""", re.I
)
SCRIPT_PRELOAD = re.compile(
    r"""<link\b[^>]*\bas\s*=\s*["']?script["']?[^>]*>|<link\b[^>]*\brel\s*=\s*["']?modulepreload["']?[^>]*>""",
    re.I,
)


def sanitize(html: str):
    report = {}

    def sub_count(pattern, replacement, text, key):
        new_text, n = pattern.subn(replacement, text)
        if n:
            report[key] = n
        return new_text

    html = sub_count(SCRIPT_BLOCK, "", html, "script blocks")
    html = sub_count(SCRIPT_SELF_CLOSING, "", html, "self-closing scripts")
    html = sub_count(SCRIPT_PRELOAD, "", html, "script preloads")
    html = sub_count(META_REFRESH, "", html, "meta refresh redirects")
    html = sub_count(EVENT_HANDLER, "", html, "inline event handlers")
    # Neutralize javascript: URLs by blanking the target, keeping the attribute.
    html = sub_count(
        JS_URL_ATTR, lambda m: f'{m.group(1)}={m.group(2)}{m.group(2)}', html,
        "javascript: URLs",
    )
    return html, report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Strip executable JS from a DOM snapshot.")
    parser.add_argument("input", help="Path to the DOM snapshot HTML file.")
    parser.add_argument("-o", "--output", help="Output path (default: <name>.sanitized.html).")
    args = parser.parse_args(argv)

    in_path = Path(args.input)
    if not in_path.is_file():
        print(f"Error: input file not found: {in_path}", file=sys.stderr)
        return 1

    html = in_path.read_text(encoding="utf-8", errors="replace")
    cleaned, report = sanitize(html)

    out_path = Path(args.output) if args.output else in_path.with_suffix(".sanitized.html")
    out_path.write_text(cleaned, encoding="utf-8")

    # Verify nothing executable slipped through.
    leftover_scripts = len(re.findall(r"<script\b", cleaned, re.I))

    print(f"Sanitized: {in_path.name} -> {out_path}", file=sys.stderr)
    if report:
        for key, n in report.items():
            print(f"  removed {n} {key}", file=sys.stderr)
    else:
        print("  nothing to remove (no executable JS found)", file=sys.stderr)
    print(f"  size: {len(html):,} -> {len(cleaned):,} bytes", file=sys.stderr)
    if leftover_scripts:
        print(f"  WARNING: {leftover_scripts} <script tag(s) still present", file=sys.stderr)
        return 2
    print("  verified: 0 script tags remain", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
