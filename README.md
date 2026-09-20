# BorrowCalc

Free mortgage, auto and personal loan calculators. Static site, zero external
requests, all maths runs client-side.

## Why it is built this way

**Speed.** CSS, JavaScript and the favicon are inlined into each page. The browser
makes exactly one request — the HTML — and the page is fully interactive. There is
no webfont, no framework, no CDN script, and therefore nothing that can block
rendering. The mortgage page is 20.6 KB raw, ~7 KB gzipped.

**Privacy.** Every calculation runs in the visitor's browser. Home price, income,
loan balance and rate are never transmitted, because there is no server-side
calculation to send them to. Competing calculators commonly harvest these inputs
as lender leads; this one cannot, by construction.

**Correctness.** Loan maths is YMYL content. The amortisation formula is printed on
every calculator page, and the schedule charges interest on the balance actually
remaining each month rather than approximating.

## Build

```bash
python make.py     # -> dist/
```

No dependencies beyond the Python standard library.

## Layout

```
build.py   document shell, design system, write helpers
pages.py   mortgage calculator: markup + client-side engine
make.py    page definitions, generic loan template, sitemap + robots
dist/      generated output — deploy this
```

Pages are data, not files. Adding a calculator or a per-state variant means
appending a dict in `make.py`, not copying HTML.

## Deploy

Any static host. `dist/` is committed, so it also works with no build step:

- **Cloudflare Pages** — build `python make.py`, output `dist` (or point at `dist`
  directly and leave the build command empty)
- **GitHub Pages / Netlify / S3** — serve `dist/`

## Verified

Payment maths is checked against reference figures, including the 0% APR branch
that divides by zero in the standard formula:

| Case | Computed | Expected |
|---|---|---|
| $320k @ 6.5% / 30yr | 2022.62 | 2022.62 |
| $200k @ 5% / 30yr | 1073.64 | 1073.64 |
| $300k @ 7% / 15yr | 2696.48 | 2696.48 |
| $30k @ 0% / 5yr | 500.00 | 500.00 |

Schedules amortise to a 0.000000 balance and reconcile against
`months × payment`.

## Licence

MIT
