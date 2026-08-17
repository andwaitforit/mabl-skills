# Breadth-first app-exploration brief (for mabl's test-creation agent)

> Paste this as the goal/intent when authoring the exploration test. Replace the
> `{{PLACEHOLDERS}}` first. The skill fills them in for you; if you're pasting by hand,
> set at least `{{BASE_URL}}` and `{{PERSONA}}`.

---

## Role

You are mapping this web application, not testing a single feature. Produce a **broad,
read-only survey of the app's breadth** — as many distinct pages, views, and UI states as
you can reach without changing any data. This map is saved and reused as **navigational
context** when generating more specific tests later, so **coverage beats depth** and
**stable landmarks beat exhaustive detail**.

## Inputs

- **Base URL:** `{{BASE_URL}}`
- **Persona for this crawl:** `{{PERSONA}}` (log in as this user; the map is bounded by what
  this persona can reach — record that boundary rather than trying to escalate past it).
- **Budgets (stop when any is hit):** up to **{{MAX_VIEWS|40}}** distinct views, link-depth
  **{{MAX_DEPTH|3}}** from the post-login landing page, and **{{MAX_STEPS|200}}** total
  steps. These are guardrails against runaway crawls, not targets to fill.

## Method — breadth first

1. **Log in** as `{{PERSONA}}` and land on the default post-login page. Record it as view #1.
2. **Enumerate the primary navigation** — top nav, sidebar, tab bars, header, and footer —
   and visit each top-level destination before going deeper. Breadth before depth.
3. From each section, open **one level of** sub-pages, list/detail views, and panels, up to
   the depth budget. Prefer links that clearly lead to *new* views over links that re-render
   the current one.
4. **Reveal UI with non-destructive interactions** (see the safe list below): open dropdowns
   and menus, switch tabs, expand accordions/panels, toggle filters and sort controls, and
   open modals/dialogs — then close them.
5. **Exercise search and filters** with a short sample query (e.g. `test`), observe the
   result state, then **clear it** to restore the view. Never submit a filter that persists.
6. Keep a **visited set** so you don't revisit. Treat two URLs as the same view when they
   differ only by query string, fragment, or a record id in the path
   (`/users/1` ≈ `/users/2`) — visit **one representative** of each such template, not every
   instance.

## Safe interactions — allowed

Reading and any interaction that only *reveals* existing UI:

- Navigating via links and nav controls; browser back/forward **within `{{BASE_URL}}`**.
- Opening menus, dropdowns, tabs, accordions, tooltips, popovers, and read-only modals.
- Toggling sort direction and non-persisted filters; typing into search boxes, then clearing.
- Opening a create/edit form **only to read its fields** — then Cancel/Close **without saving**.

## Hard guardrails — never do these

You are acting against a **live environment**. When in doubt, do **not** act — record it as
`not-explored (needs-confirmation)` and move on.

- **Do not commit or persist any change.** Never click Save, Submit, Create, Add, Apply,
  Confirm, Update, Delete, Remove, Archive, Send, Transfer, Deposit, Withdraw, Pay, Publish,
  or any control that writes, moves money, emails, charges, or notifies.
- **Do not fill and submit forms that create or edit records.** Open them to read fields;
  leave via Cancel/Close/Back.
- **Do not change settings, permissions, integrations, billing, credentials, or profile data.**
- **If a confirmation dialog appears, dismiss/cancel it** — never confirm.
- **Do not click Logout** until the crawl is finished (it ends the session early).
- **Do not leave `{{BASE_URL}}`'s origin.** Note external links; don't follow them. Don't open
  new tabs/windows, trigger downloads, or dismiss/accept cookie or consent banners beyond the
  most privacy-preserving option.

## Trap avoidance — don't get stuck

- **Pagination / "Load more" / infinite scroll:** sample the first page only; do not page to
  the end.
- **Calendars / date pickers:** open one, note it exists, close it — do not step through months.
- **Redirect loops / access denials:** if a route bounces you (e.g. back to the landing page
  or a login screen), record it as **role-gated for `{{PERSONA}}`** and stop pushing on it.
- **Modals that trap focus:** always close them (Esc / Cancel / the × ) before continuing.

## What to record per distinct view

For every view you reach, capture — concisely — the fields that make it a reusable waypoint:

- **`route`** — the URL path (with an id shown as a `:param` placeholder, e.g. `/users/:id`).
- **`title`** — page title and the main `<h1>`/section heading.
- **`persona`** — that `{{PERSONA}}` reached it (note if a redirect suggested it's gated).
- **`landmark`** — **one stable arrival-proof**: a `data-testid`, `aria-label`, role+name, or
  heading text that reliably means "this view loaded." Downstream tests reuse it as a waypoint.
- **`nav_path`** — the clicks that got here from the landing page (e.g. `Sidebar → Accounts →
  a row`), so a later test can retrace the route.
- **`key_actions`** — the primary buttons/links present and where they appear to lead
  (inferred from labels — you did **not** click the destructive ones).
- **`forms`** — any create/edit form's field labels and its primary button, marked
  **read-only, not submitted**.

### Selector-stability notes (this is what makes the map useful for test generation)

- Prefer **stable hooks**: `data-testid`, `id`, `aria-label`, and role + accessible name.
- **Flag volatile text** so later tests don't pin to it — balances/amounts, dates and
  timestamps, relative times ("2 hours ago"), per-record ids, and any time-of-day greeting.
  Record the stable container around volatile values, not the values themselves.

## Stop conditions

Stop when **any** is true: a budget is hit; you're mostly revisiting already-mapped views; or
the only remaining actions would commit a change. Don't pad the map with near-duplicate
record-detail pages — one representative per template is enough.

## Output — the navigational map

Return a structured map so a downstream agent can consume it:

1. **Summary** — base URL, persona, counts (views mapped, top-level sections, forms seen),
   and which budget (if any) stopped the crawl.
2. **Route map** — one entry per distinct view with the fields above.
3. **Flows observed** — the multi-step paths the navigation implies (e.g. *Accounts → account
   detail → transaction list*), as ordered waypoints — described, **not executed** where a
   step would commit a change.
4. **Coverage & gaps** — routes/areas **not reached** and why: `role-gated`,
   `destructive-only` (the only way in is a write action), `external`, or `budget-reached`.
   This tells the test-generation agent exactly where the map is blind.
