# 'Xia Design System

> AI-powered resume and portfolio builder. Premium, editorial, warm, tech-forward.

'Xia turns a person's raw career history into two finished outputs: a live hosted portfolio site and an ATS-optimized resume. The product is organized around three AI agents — **Resume Parsing**, **Dynamic Portfolio Generation**, and **ATS Optimization** — all reading from one single-source-of-truth profile.

The brand voice is the same standard the product enforces on its users' resumes: confident, active, grounded, specific, free of buzzwords. The mark is an apple drawn as an open outline, gradient-stroked deep violet → coral, with botanical elements (leaf, branching stem, sparkle, coral dot) inside.

---

## Index

| File                         | What's in it                                         |
| ---------------------------- | ---------------------------------------------------- |
| `colors_and_type.css`        | All tokens — palette, neutrals, type, spacing, radii, shadows, motion |
| `assets/xia-logo.png`        | Primary logo mark — apple outline, gradient, transparent BG |
| `assets/xia-apple-mark.jpg`  | Larger source render of the mark (1254×1254)         |
| `preview/`                   | Design system cards shown in the DS tab              |
| `ui_kits/website/`           | Marketing site components + screen recreations       |
| `ui_kits/product/`           | In-product builder & Resume AI workshop              |
| `SKILL.md`                   | Agent-Skill entrypoint (drop into Claude Code)       |

---

## Source materials

- Local upload: `uploads/xia_website.html` — the production marketing site, fully self-contained (~2700 lines). Treat this as the source of truth for visuals, copy, motion, and component shapes.
- Local upload: `uploads/6080335461390946281.jpg` (also at `assets/xia-apple-mark.jpg`) — full-resolution apple mark.
- GitHub: [`meitongkim/xiacareer.io`](https://github.com/meitongkim/xiacareer.io) (private; was empty at time of build — the marketing HTML was the only deliverable). If/when this fills out, re-explore for the in-product app code.
- Other repos by the same designer worth a look for stylistic context: [`meitongkim/meitongkim.github.io`](https://github.com/meitongkim/meitongkim.github.io), [`meitongkim/claeb.io`](https://github.com/meitongkim/claeb.io), [`meitongkim/memoire-photobooth`](https://github.com/meitongkim/memoire-photobooth).

---

## Content fundamentals

The voice mirrors what 'Xia asks its users to do: lead with concrete numbers, prefer strong verbs over adjectives, and never oversell. The reader is treated as a capable professional, not a target.

- **Person:** Mostly second-person ("Your career, beautifully built", "Upload your resume"). The brand drops into first-person plural for the About section only ("We built the AI portfolio builder we wish we'd had").
- **Casing:** Title Case in nav items, button labels, and section titles. Sentence case in body copy. UPPERCASE with +2px tracking reserved for eyebrow labels ("CORE CAPABILITIES", "GETTING STARTED").
- **Capitalization quirk:** The brand name carries a **leading apostrophe** — write `'Xia`, never `Xia`. Inside copy this reads like a hush before a name, which is the intended mood.
- **Numbers up front:** "<3s resume parsed", "94% avg. ATS pass-through", "58K+ portfolios published", "in under 10 minutes", "22% ($140K ARR)". Pricing is always real ("$0", "$19/mo"), never "starting at."
- **Verbs do the work:** *Led, Built, Designed, Mentored, Reduced.* Never *Responsible for, Helped with, Worked on.* The Resume AI workshop UI quite literally crosses these out.
- **Tone segments:** The product offers a three-step register — Grounded / Balanced / Confident — and the marketing copy itself sits on "Balanced": clear and active, without overselling. This is the default tone for everything you write.
- **Forbidden register:** No buzzwords ("synergize", "bleeding-edge", "revolutionize", "leverage"). The product literally exposes a buzzword-density meter; the marketing must clear its own bar.
- **Emoji:** Used sparingly as small inline glyphs inside the product UI — ⚡ for the parsing agent, 🎨 for portfolio gen, 📊 for ATS, 📄/🚀/💼/📋 inside step icons. Never in headlines, never decorating CTAs, never in copy paragraphs. Treat them as miniature icons, not punctuation.
- **The three-part opener:** Every section opens with the same rhythm — small uppercase **eyebrow** ("CORE CAPABILITIES"), then a heavy Syne H2 with a hard line break, then a light 300-weight lead paragraph. This is the recurring drumbeat of the brand.

Examples:
- Eyebrow → "Core Capabilities"
- H2     → "Three AI agents. / One career identity."
- Lead   → "Each agent is purpose-built for a different layer of your career brand — from raw document to polished live site."

- Hero H1 uses inline color contrast on the punchline word: "Your career, **beautifully built**" — *beautifully built* sits in coral against ink for the rest.
- CTA copy is verb-first and free of friction language: "Start Building Free", "See the Features", "View Live Preview", "Strengthen with AI", "Analyze fit & tailor". No "Click here." No "Learn more."

---

## Visual foundations

### Colors

Five brand colors, four of them in the violet family, anchored by a single warm coral. The hierarchy rule is **saturation = importance**:

| Token        | Hex       | Role                                                          |
| ------------ | --------- | ------------------------------------------------------------- |
| `--ink`      | `#201020` | Headings, body text, dark section backgrounds                 |
| `--deep` / `--g800` | `#3c2a4b` | Secondary dark surfaces                                |
| `--velvet`   | `#5d396d` | **Hover only** for primary accent                             |
| `--indigo`   | `#8b60a5` | Primary accent — buttons, links, rings, active states         |
| `--coral`    | `#e39797` | Warm highlight — eyebrow badges, hero accent word, glows      |

Coral is never a primary action color — it is reserved for moments of warmth and emphasis. Velvet is **exclusively** the hover deepening of indigo, never a fill.

Neutrals are warm, lavender-tinted (`#f3eef9` → `#3c2a4b`), not neutral gray. This is what keeps grays feeling like part of the violet family instead of dropping into corporate-Material territory.

One important exception governs the simulated user portfolios and resumes inside the preview area: those mockups use neutral non-brand colors (slate, mint, indigo blue) because they represent someone else's work, not the 'Xia interface itself.

### Type

| Use                                       | Family + weight | Size                | Tracking      |
| ----------------------------------------- | --------------- | ------------------- | ------------- |
| Hero H1                                   | Syne 800        | `clamp(44–84px)`    | −2.5px        |
| Section H2                                | Syne 700        | `clamp(28–46px)`    | −1.2px        |
| Card title (H3/H4), stats                 | Syne 700        | 15–17px / 28–46px   | −0.3px        |
| Eyebrow (`.eyebrow` / `.stag`)            | DM Sans 600     | 11px                | +2px, UPPERCASE |
| Lead paragraph                            | DM Sans 300     | 17px                | normal        |
| Body                                      | DM Sans 400     | 16px / 1.6 lh       | normal        |
| UI label                                  | DM Sans 500–600 | 11–14px             | normal        |
| Code / URLs                               | system mono     | 11–13px             | normal        |

The light-weight 300 lead paragraph beneath a heavy 700–800 Syne headline is the system's signature contrast.

### Spacing & layout

- Main content column: **1100px**. Focused product flows (builder wizard, resume workshop): **960px**.
- Section padding: **96px** desktop / **64px** mobile vertical; **2rem** desktop / **1.25rem** mobile horizontal.
- Fixed nav: **62px** tall, white-with-88%-alpha, `backdrop-filter: blur(20px) saturate(180%)`, 1px bottom border.
- Breakpoints: `1000px` (grids collapse), `900px` (nav → hamburger, two-column → stack), `640px`, `400px`.

### Radii

| Use                           | Radius   |
| ----------------------------- | -------- |
| Buttons, inputs               | 8–11px   |
| Cards, mockup windows         | 16–20px  |
| Pills, chips, toggles         | 100px    |
| Small inline elements         | 5–10px   |

### Elevation

Shadows are **always purple-tinted** (never neutral black). This keeps depth feeling like part of the palette:

```
--shadow-card:  0 14px 44px rgba(93,57,109,.14);   /* card hover    */
--shadow-mock:  0 24px 72px rgba(60,42,75,.10);    /* browser mock  */
--shadow-btn:   0 10px 28px rgba(139,96,165,.30);  /* primary CTA   */
```

### Backgrounds & atmosphere

- **Off-white sections** (`#f8f4fc`) alternate with white to give vertical rhythm. The `--ink` background is reserved for **section-final emphasis** — the stats strip, the closing CTA, and the footer.
- **Drifting mesh-gradient orbs** sit behind the hero — three blurred radial blobs in coral / indigo / deep-violet, looping on 22–30s ease-in-out drifts. Filter: `blur(70px)`. They are the brand's signature ambient layer.
- **Radial protection gradient** on the ink CTA section (`radial-gradient(ellipse 70% 60% at 50% 0%, rgba(139,96,165,.18), transparent)`).
- **No raster background photos.** No grain. No hand illustrations. The decorative weight is carried by the orbs, the eyebrow rhythm, and Syne's geometry.
- **Borders** are 1–1.5px in `--g100`/`--g200`. Strong borders (1.5–2px) only on selected cards and inputs at focus. Two-pixel underlines (`border-bottom: 2px solid var(--ink)`) on resume section headers — a deliberate ATS-formality cue.

### Motion

One signature easing: **`cubic-bezier(.22, 1, .36, 1)`** — applied to essentially every transition.

| Tier                    | Duration   | Used for                                |
| ----------------------- | ---------- | --------------------------------------- |
| Micro                   | 150–200ms  | Hover color shifts, focus, tab swaps    |
| Standard                | 300–400ms  | Tab content transitions, panel reveals  |
| Scroll reveal           | 700–850ms  | Section fade-up / scale-with-unblur     |
| Count-up                | ~1200ms    | Stat numbers, progress rings            |

Established animation vocabulary:
- **Word-by-word headline reveal** — each word rises with a slight rotation.
- **Drifting gradient orbs** behind the hero (22–30s loops).
- **Magnetic buttons** that lean toward the cursor; with a coral/indigo glow ring on hover.
- **3D tilt** on the hero dashboard, driven by mouse position.
- **Self-generating portfolio preview** — sections fade-up one by one when scrolled into view, paired with a progress sweep across the browser chrome.
- **Two scroll-reveal flavors:** `.rv` (fade + 22px translateY) and `.rv-scale` (scale 0.94 → 1 with a `blur(4px)` → 0 unblur).
- **Directional tab transitions** — panel slides from the side matching the tab's position.
- **Count-up statistics** with ease-out cubic over 1.2s.
- **Typing-dot indicators** in the AI chat (three dots translateY -5px, 0.2s stagger).
- **Stroke-dashoffset progress rings** for ATS and fit scores (1.3s ease).

All of it is gated behind a `prefers-reduced-motion` media query that disables the orbs, tilt, word animation, and auto-reveals — content stays fully visible.

### Interaction states

- **Hover (button, primary):** background flips `--indigo → --velvet`, `translateY(-2px)`, picks up the indigo glow box-shadow.
- **Hover (button, secondary):** border darkens `--g100 → --g200`, color shifts to `--ink`, `translateY(-1px)`.
- **Hover (link, anchor):** gap widens from 5px to 9px on chevron links (`a.lk`); underline stays.
- **Hover (card):** border darkens to `--g200`, picks up `--shadow-card`, `translateY(-2 to -4px)`.
- **Hover (table row, nav item):** background fills with `--g50`.
- **Active / selected:** primary background or fill becomes `--indigo`; `box-shadow: 0 0 0 3px rgba(139,96,165,.12)` ring around selected cards.
- **Press:** matches hover state (the design does not shrink-on-press — translate-up is the consistent feedback).
- **Focus:** input borders shift to `--indigo`; no separate `:focus` ring color (the border IS the ring).
- **Disabled:** `opacity: 0.3–0.4`, `pointer-events: none`.

### Transparency & blur

- Nav background: `rgba(255,255,255,0.88)` + `backdrop-filter: blur(20px) saturate(180%)`. The same recipe re-skinned dark for portfolio-mockup navs.
- Marquee edge fades: `linear-gradient(to right, white, transparent)` 72px wide on both edges.
- Dark cards on the ink section sit at `rgba(255,255,255,0.06)` background with `rgba(255,255,255,0.1)` borders.

### Cards

The recurring card shape is:
- `background: white`
- `border: 1.5px solid var(--g100)`
- `border-radius: 16–20px`
- On hover: `border-color: var(--g200)`, `box-shadow: var(--shadow-card)`, `translateY(-2 to -4px)`.
- Selected: `border-color: var(--indigo)`, `box-shadow: 0 0 0 3px rgba(139,96,165,.10)`.

There is no left-border-accent-color pattern. There are no gradient card backgrounds (except specifically the three feature-card demo wells, which use named pastel tints — indigo-tinted for parsing, mint for generation, amber for ATS — and read as "live demo terrariums," not as primary cards).

---

## Iconography

There is **no icon font** and **no SVG icon library** in the source codebase. Icons are handled in three ways, in strict priority order:

1. **Inline SVG, lucide-style** — written by hand for the small set of UI affordances: `→` arrow, ✓ check, chevron left/right, plus, x, and the magnifying glass. They use `stroke: currentColor`, `stroke-width: 2`, `stroke-linecap: round`, `stroke-linejoin: round` on a 24×24 viewBox. Treat new icons the same way: stroked, 2px, rounded caps. When you need an icon set, **import lucide from CDN** as the closest visual match (same stroke weight and joinery).
2. **Inline unicode glyphs** for atmosphere — checkmark `✓`, multiplication sign `✕`, question mark `?`, em-dash `—`, middle dot `·`, the en-dash `–`. These appear inside chips and meta rows as low-effort separators.
3. **Emoji** for the *one* "product icon" role inside cards: ⚡ (parsing), 🎨 (portfolio gen), 📊 (ATS), 📄 (upload), 🚀 (publish), 💼 (LinkedIn), 📋 (Indeed), ✏️ (paste), 🤖 (AI), 🛒, 📱, 🌐. They sit inside a 38–44px rounded square with a `--g50` background and `--g100` border. They are never placed in headlines or in body copy.

Logos used in marketing are typeset words ("Google", "Stripe", "Grab") inside marquee chips, not raster wordmarks.

> **Substitution note:** Because there is no first-party icon set, downstream pages built from this system that need a wider library should pull **[Lucide](https://lucide.dev)** from CDN. It is the closest match to the project's hand-rolled SVG style (24×24, 2px stroke, rounded). Flag the substitution in any new artifact's README.

---

## Visual previews

The `preview/` folder contains small HTML cards that populate the Design System tab — one card per sub-concept (palette, type scale, eyebrow rhythm, buttons, chip, ring, browser chrome mockup, etc). They are the fastest way to scan the system at a glance.

## UI kits

- **`ui_kits/website/`** — the marketing site. Faithful recreations of the nav, hero, feature grid, portfolio preview, builder wizard, Resume AI workshop, templates gallery, stats, pricing, testimonials, and footer. `index.html` is an interactive stitch of the components.
- **`ui_kits/product/`** — the in-product surfaces. The four-step builder wizard, the bullet workshop chat, the job-campaign analyzer, and the ATS report — extracted from the preview-tab demos that already live in the site.

Both kits load `colors_and_type.css` from the project root, so token changes propagate everywhere.
