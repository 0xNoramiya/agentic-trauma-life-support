# ATLS landing page

Next.js 15 (App Router) + Tailwind 4. The marketing front for **Agentic Trauma Life Support**, with a CTA out to the live demo on HuggingFace Spaces.

The look-and-feel reference is a serious medical or engineering journal title page — Atlantic / Stripe Press / The New York Review of Books — not a SaaS template. Restraint, weight, confidence.

## Run locally

```bash
cd landing
npm install
npm run dev
```

Open `http://localhost:3000`.

## Deploy to Vercel

The simplest path: push this repo to GitHub, then on Vercel click **Add New → Project** and select the repo. Set **Root Directory** to `landing`. No environment variables required — this is a pure static-friendly marketing site.

Or via the CLI from `landing/`:

```bash
npx vercel        # one-time setup
npx vercel --prod # ship production
```

## What this is and is not

**Is:** a typographic landing page that explains the project, the agentic pipeline, the single-MI300X argument, the real benchmarks, the six demo cases, and links out to the live demo and the engineering writeup.

**Is not:** an inference UI. The actual triage tool lives on the HuggingFace Space, served directly from the MI300X. This page is purely additive — it changes nothing in the parent repo's `src/`, `space/`, `scripts/`, or `docs/`.

## File map

```
landing/
├── package.json           Next.js 15 + React 19 + Tailwind 4
├── next.config.mjs        minimal config
├── postcss.config.mjs     Tailwind 4 via @tailwindcss/postcss
├── tsconfig.json          standard Next.js TS config
└── src/
    ├── app/
    │   ├── layout.tsx     fonts (Source Serif 4 + IBM Plex Sans/Mono) + metadata
    │   ├── page.tsx       single-page composition
    │   └── globals.css    Tailwind import, @theme tokens, drop-cap, hero stagger
    └── components/
        ├── Hero.tsx                title page + CTAs
        ├── SectionLabel.tsx        the § marker
        ├── DoubleMeaning.tsx       editorial block w/ marginalia + drop cap
        ├── WhyThisExists.tsx       editorial block w/ marginalia + drop cap
        ├── MemoryMath.tsx          GPU-shortlist bar figure with 145 GB threshold
        ├── Pipeline.tsx            Drafter / Verifier* / Renderer cards
        ├── Benchmarks.tsx          three big stats (TTFT / throughput / VRAM)
        ├── DemoCases.tsx           2×3 grid of cases
        ├── CredibilityMoment.tsx   pull quote w/ oversized terracotta opening "
        ├── ShipsWith.tsx           seven-row colophon
        └── Closing.tsx             ATLS wordmark + sign-off
```

## Design tokens

Defined in `src/app/globals.css` under `@theme`:

| Role             | Token              | Hex       |
| ---------------- | ------------------ | --------- |
| Paper canvas     | `--color-paper`    | `#F8F7F4` |
| Subtle band      | `--color-paper-2`  | `#F3F1EC` |
| Primary text     | `--color-ink`      | `#1A1F2E` |
| Sage accent      | `--color-sage`     | `#3A7A6E` |
| Hairlines        | `--color-hairline` | `#D9D6D0` |
| Terracotta       | `--color-terracotta` | `#B8463A` |

Used as Tailwind utilities: `bg-paper`, `text-ink`, `border-sage`, `text-terracotta`, etc.

Fonts loaded via `next/font/google`:

- **Display** — Source Serif 4 (400 / 600 / 700, italic)
- **Body** — IBM Plex Sans (300 / 400 / 500 / 600)
- **Mono** — IBM Plex Mono (400 / 500)

## Editorial details worth keeping

- `§ 01` through `§ 07` section markers replace conventional headers — typeset like printed journal chapter marks
- Drop caps on §01 and §02 (in sage)
- Marginalia in the gutter on §01 and §02 (a small italic note like NYRB)
- Single terracotta accent — appears once on the verifier asterisk, once on case 05's hairline + caption, once on the credibility-moment opening quote, and once on the case 05 language tag. That's the budget.
- A 0.018-opacity radial-dot grain over the entire page (paper texture, not visible at first glance)
- Hero entrance is a CSS-keyframe staggered fade-up (subhead → headline → body → CTAs → colophon). Respects `prefers-reduced-motion`.
- All sections below the fold render statically — no scroll observers, no client JS for animation

## Anti-patterns (intentionally avoided)

- Glowing-brain / neural-mesh / holographic-doctor imagery
- Gradient backgrounds (purple-to-pink, etc.)
- Inter / Roboto / Arial as display fonts
- SaaS hero illustration
- "Trusted by [logos]" social-proof rows
- Stock photos of any kind
