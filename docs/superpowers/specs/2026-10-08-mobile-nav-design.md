# Mobile Navigation — Design

**Date:** 2026-10-08
**Status:** Approved

## Purpose

Below 600px the navigation is hidden entirely, so a mobile visitor sees only
the logo and has no way to reach `/articles/` or `/model-registry/`. Two of the
four sections are unreachable except by typing a URL.

## Goals

- All four nav items reachable on a phone, without JavaScript.
- Desktop navigation unchanged: four links in one row, no burger.
- Keyboard and screen-reader operable.

## Non-goals

- No slide-in animation, no backdrop overlay, no close-on-outside-click.
- No change to `main.js`.
- No change to the desktop nav markup beyond wrapping it.

## Why `details`/`summary`

The four links cannot fit on one 375px row: after the nav's `2rem` padding only
311px remain, and the Georgia logo takes roughly 165px of it.

The chosen mechanism is the native `<details>`/`<summary>` pair rather than a
`<button>` toggled from JavaScript. It works with scripting disabled or blocked,
which matters for a site whose only other script is a mailto de-obfuscator. A
JS `<button>` would leave the button inert when the script fails, which is
strictly worse than the current state.

## Markup

In `templates/base.html`, the nav links move inside a `details` element:

```html
<nav>
    <a class="logo" href="/#principles">Business Model Hub</a>
    <details class="nav-menu">
        <summary>
            <span class="nav-burger" aria-hidden="true"></span>
            <span class="sr-only">Menu</span>
        </summary>
        <div class="nav-links">
            <a href="/#principles"{% if nav_active == "principles" %} class="active"{% endif %}>Principles</a>
            <a href="/model-registry/"{% if nav_active == "registry" %} class="active"{% endif %}>Registry</a>
            <a href="/articles/"{% if nav_active == "articles" %} class="active"{% endif %}>Articles</a>
            <a href="/#contact"{% if nav_active == "contact" %} class="active"{% endif %}>Contact</a>
        </div>
    </details>
</nav>
```

The four links and their `nav_active` conditions are unchanged; only their
position in the tree changes.

## Desktop, above 600px

Two rules in `@media (min-width: 601px)`:

```css
.nav-menu > summary {
    display: none;
}

.nav-menu > .nav-links {
    display: flex;
    content-visibility: visible;
}
```

A closed `<details>` hides its children through a user-agent rule. Overriding it
needs both declarations: `display` for the classic UA rule, and
`content-visibility` for the newer Chrome behaviour where closed details are
hidden via `content-visibility: hidden` rather than `display`.

**This is the one part of the design that cannot be verified without a real
browser.** If a specific browser keeps the links hidden on desktop, the fix is
confined to these two declarations.

Because the links are forced visible regardless of the `open` attribute, a
mobile user who opens the menu and rotates to desktop sees no layout glitch.

## Mobile, at 600px and below

The existing `.nav-links { display: none; }` is removed. In its place:

- `summary` is displayed as the burger control, aligned to the right of the
  logo by the nav's existing `justify-content: space-between`.
- `.nav-burger` is three bars drawn with a `linear-gradient` background.
- `.nav-menu[open] .nav-burger` switches the background to a cross.
- `.nav-links` becomes a panel: `position: absolute`, `top: 100%`,
  `left: 0`, `right: 0`, vertical column, `background: var(--bg)` so text stays
  readable over the page behind it.

`nav` is already `position: sticky`, so `top: 100%` anchors the panel directly
beneath the bar without extra positioning context.

## Accessibility

`<summary>` is natively focusable and operable with Enter and Space, and screen
readers announce it as a disclosure control. Therefore:

- No `aria-expanded` — it is implicit, and adding it manually to a `summary`
  conflicts with the native semantics.
- No `role` or `tabindex` on the burger.
- The icon span is `aria-hidden="true"`; adjacent `.sr-only` text supplies the
  accessible name.

`.sr-only` is added to the stylesheet using the standard clip-based pattern; it
does not exist in the current CSS.

## Side change: nav padding

The nav keeps `padding: 0.9rem 2rem` at all widths, while `header` and `main`
drop to `1rem` below 600px. The bar is therefore inset differently from the
page. The mobile query adds `padding-left: 1rem; padding-right: 1rem` for `nav`.

The nav's `max-width: 900px` is unaffected.

## Testing

`tests/test_base.py`:

- the rendered nav contains `<details class="nav-menu">` and a `<summary>`
- the summary carries the accessible name text `Menu`
- the four hrefs and their `nav_active` behaviour are unchanged (already
  covered by the existing nav tests)

`tests/test_assets.py`:

- `.nav-burger` exists in the stylesheet
- the mobile query no longer sets `display: none` on `.nav-links`
- `.sr-only` exists in the stylesheet

`main.js` is not modified, and its existing test is unchanged.

## Verification limits

The build and the test suite can confirm the markup and the CSS rules exist, but
cannot confirm rendering. Two things need a real browser:

- the closed `details` override on desktop
- the panel position and burger appearance at 375px

Both are called out in the design above rather than claimed as verified.
