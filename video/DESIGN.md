# Visual identity — ATLS demo video

## Style Prompt

Clinical editorial. Off-white canvas, deep ink, one muted-sage accent. Display serif for headlines, geometric sans for body. Generous negative space, architectural symmetry. Numbers and labels are quiet — nothing screams. The aesthetic comes from confidence in the content, not from typography or motion. Think *editorial print* (a serious medical journal cover), not *SaaS dashboard.*

Inspired by Velvet Standard (Vignelli — architectural symmetry, single accent, generous space) but in a light/clinical palette rather than luxury black/gold. The accent is muted sage — medical-adjacent, calming, deliberately not "tech blue." A single critical-red is reserved for the case-05 red-flag callout and used nowhere else.

## Colors

| Role | Hex | Notes |
|---|---|---|
| Canvas (background) | `#F8F7F4` | Warm paper. Never pure white — pure white reads sterile/cold |
| Primary text | `#1A1F2E` | Deep ink. Headlines, body |
| Secondary text | `#5A6273` | Captions, labels, metadata |
| Accent | `#3A7A6E` | Muted medical sage. Used sparingly — language toggle, MI300X bar highlight, link underlines |
| Critical highlight | `#B8463A` | Terracotta-red. Used **once**, for the red-flag callout in scene 7 |
| Hairline / dividers | `#D9D6D0` | 1 px hairline, when needed |

## Typography

- **Display headline:** `'Source Serif 4', 'Tinos', 'EB Garamond', serif` — 80–120 px on display scenes, line-height 1.05, weight 600, never italic
- **Body / captions:** `'Inter', system-ui, sans-serif` — 22–32 px, weight 400, line-height 1.5
- **Labels / SMALL CAPS:** `'Inter', system-ui, sans-serif` — 16–18 px, weight 600, `letter-spacing: 0.12em`, `text-transform: uppercase`
- **Numerals (memory math, GB, $/hr):** add `font-variant-numeric: tabular-nums` so columns align
- **Pull quotes (scene 7):** display serif italic, 60–72 px, indented; opening quotation mark in accent sage

## Motion rules

- **Easing:** `power2.out` for entrances (calm, decelerating). Never `bounce`, never `back.out` overshoot. Never `linear`.
- **Stagger:** 100–150 ms between sibling elements (a tick more than the house default — slightly slower keeps the clinical tone)
- **Entrance type:** opacity + small `y` offset (≤ 30 px). No scale-from-zero. No flying-in from offscreen.
- **Hold:** every scene's hero frame holds for 1.5–2 s before transition fires. Don't pack scenes — let content breathe.
- **Transitions:** soft cross-dissolves only. No wipes, no whips, no glitch, no shader transitions. Scene-to-scene feels like turning a page in a journal.

## What NOT to do

1. **No gradients on the canvas.** Solid `#F8F7F4` only. Gradients on light-canvas video tend to band on H.264; more importantly, they push toward "SaaS landing page" aesthetic which is exactly the opposite of what this is.
2. **No bright accent colors.** The sage is at 50% saturation deliberately. Never reach for `#3b82f6`, `#0066FF`, or any bright tech blue. The terracotta is the loudest color we use, and only for one moment.
3. **No icons or illustrations beyond the four functional ones in scene 3.** The chest-X-ray / typed-vitals / language-toggle / handoff-document set is functional shorthand for the action loop — they need to be line-art, monochrome (deep ink), no color fill, no flat-design playfulness. If the scene-3 icons start looking decorative, replace with text.
4. **No scaling animations on text.** Text fades and slides in by 20–30 px. It does not pop, scale, or bounce. Scaling text reads as "tech demo product launch" — wrong genre.
5. **No code blocks or terminal screenshots.** This is the "not too techie" rule made concrete. Even on the pipeline scene (scene 5), boxes are labeled with words, not code. The benchmarks scene shows GB values, not flag names.
