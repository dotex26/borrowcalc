#!/usr/bin/env python3
"""BorrowCalc static site generator.

Design goals, in priority order:
  1. Speed. Zero external requests - CSS, JS, fonts and icons are all inline
     or system-native. No render-blocking resource exists, so LCP is bounded
     only by the HTML download itself.
  2. Correctness. Loan maths is YMYL content; formulas are stated openly and
     computed in double precision, rounded only for display.
  3. Scale. Pages are data, not files. Adding 50 US state variants later means
     appending to a list, not copying HTML.

Output: dist/ - deploy anywhere static (Cloudflare Pages, Netlify, S3).
Run: python build.py
"""
import os
import json
import datetime

SITE = "https://borrowcalc.com"
NAME = "BorrowCalc"
ROOT = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(ROOT, "dist")
YEAR = datetime.date.today().year

NAVY = "#12284B"

LOGO = (
    '<svg viewBox="0 0 64 64" class="mark" aria-hidden="true">'
    '<rect x="10" y="4" width="44" height="56" rx="8" fill="#12284B"/>'
    '<rect x="17" y="11" width="30" height="16" rx="4" fill="#fff"/>'
    '<g fill="#0FA968"><circle cx="25.5" cy="15.5" r="2.7"/>'
    '<circle cx="38.5" cy="22.5" r="2.7"/>'
    '<rect x="30.7" y="12.5" width="2.6" height="13" rx="1.3" transform="rotate(33 32 19)"/></g>'
    '<g fill="#fff"><rect x="17" y="33" width="8.5" height="7" rx="2.2"/>'
    '<rect x="27.8" y="33" width="8.5" height="7" rx="2.2"/>'
    '<rect x="17" y="43" width="8.5" height="7" rx="2.2"/>'
    '<rect x="27.8" y="43" width="8.5" height="7" rx="2.2"/>'
    '<rect x="17" y="53" width="19.3" height="4.5" rx="2.2"/></g>'
    '<rect x="38.6" y="33" width="8.5" height="24.5" rx="2.6" fill="#0FA968"/></svg>'
)

# Favicon as a data URI: one less network request, and it can never 404.
FAVICON = (
    "data:image/svg+xml,"
    "%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E"
    "%3Crect width='64' height='64' rx='12' fill='%2312284B'/%3E"
    "%3Cg fill='%230FA968'%3E%3Ccircle cx='24' cy='24' r='5'/%3E"
    "%3Ccircle cx='40' cy='40' r='5'/%3E"
    "%3Crect x='29.5' y='14' width='5' height='36' rx='2.5' transform='rotate(35 32 32)'/%3E"
    "%3C/g%3E%3C/svg%3E"
)

# System font stack: renders instantly, zero network cost, matches the user's
# OS. A webfont would cost ~100KB and a render-blocking request for no benefit
# a finance tool can actually use.
CSS = """*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
:root{--navy:#12284B;--em:#0FA968;--slate:#5A6B87;--cloud:#F4F7FB;--line:#E2E8F2}
html{-webkit-text-size-adjust:100%}
body{font:16px/1.65 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif;
color:var(--navy);background:var(--cloud);text-rendering:optimizeLegibility}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
a{color:var(--navy);text-decoration:none}a:hover{text-decoration:underline}
header{background:#fff;border-bottom:1px solid var(--line);position:sticky;top:0;z-index:20}
.hrow{display:flex;align-items:center;gap:24px;height:64px}
.logo{display:flex;align-items:center;gap:9px;font-weight:800;font-size:20px;letter-spacing:-.4px}
.logo em{font-style:normal;color:var(--em)}
.mark{width:26px;height:26px;flex:0 0 26px}
nav{margin-left:auto;display:flex;gap:22px;font-size:14.5px;font-weight:600}
nav a{color:var(--slate)}
@media(max-width:760px){nav{display:none}}
h1{font-size:clamp(28px,4.2vw,42px);line-height:1.15;letter-spacing:-1px;font-weight:800}
h2{font-size:clamp(21px,2.6vw,27px);line-height:1.25;letter-spacing:-.5px;font-weight:800;margin-bottom:12px}
h3{font-size:18px;font-weight:700;margin-bottom:8px}
.lead{font-size:18px;color:var(--slate);margin-top:12px;max-width:62ch}
.hero{padding:44px 0 26px}
section{padding:32px 0}
.card{background:#fff;border:1px solid var(--line);border-radius:14px;padding:22px}
.calc{display:grid;grid-template-columns:1fr 1fr;gap:20px;align-items:start}
@media(max-width:860px){.calc{grid-template-columns:1fr}}
.fields{display:grid;gap:15px}
.f label{display:block;font-size:13.5px;font-weight:700;margin-bottom:5px}
.f .hint{font-weight:500;color:var(--slate);font-size:12.5px}
.ip{display:flex;align-items:center;background:#fff;border:1.5px solid var(--line);border-radius:9px;overflow:hidden}
.ip:focus-within{border-color:var(--em)}
.ip s{font-style:normal;text-decoration:none;padding:0 11px;color:var(--slate);font-weight:700;font-size:14px;
background:var(--cloud);align-self:stretch;display:flex;align-items:center}
.ip input{border:0;outline:0;padding:11px;font:inherit;font-weight:700;width:100%;min-width:0;color:var(--navy)}
.ip input::-webkit-outer-spin-button,.ip input::-webkit-inner-spin-button{-webkit-appearance:none;margin:0}
.ip input[type=number]{-moz-appearance:textfield}
.two{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.res{background:var(--navy);color:#fff;border-radius:14px;padding:24px;position:sticky;top:84px}
@media(max-width:860px){.res{position:static}}
.res .big{font-size:clamp(34px,5.4vw,46px);font-weight:800;letter-spacing:-1.5px;line-height:1.05;
font-variant-numeric:tabular-nums}
.res .cap{font-size:13px;text-transform:uppercase;letter-spacing:1.1px;color:#9DB2D4;font-weight:700}
.bd{margin-top:18px;border-top:1px solid rgba(255,255,255,.16);padding-top:14px;display:grid;gap:9px}
.bd div,.tot div{display:flex;justify-content:space-between;font-size:14.5px;color:#DCE5F3}
.bd b{color:#fff;font-variant-numeric:tabular-nums}
.tot{margin-top:16px;padding-top:14px;border-top:1px solid rgba(255,255,255,.16);display:grid;gap:9px}
.tot b{color:var(--em);font-variant-numeric:tabular-nums}
.bar{display:flex;height:9px;border-radius:5px;overflow:hidden;margin-top:16px;background:rgba(255,255,255,.14)}
.bar i{display:block;height:100%}
.key{display:flex;gap:14px;flex-wrap:wrap;margin-top:10px;font-size:12.5px;color:#9DB2D4}
.key b{display:inline-block;width:9px;height:9px;border-radius:3px;margin-right:5px;vertical-align:middle}
.tbl{width:100%;border-collapse:collapse;font-size:14px;font-variant-numeric:tabular-nums}
.tbl th,.tbl td{padding:9px 10px;text-align:right;border-bottom:1px solid var(--line)}
.tbl th{font-size:12px;text-transform:uppercase;letter-spacing:.7px;color:var(--slate)}
.tbl th:first-child,.tbl td:first-child{text-align:left}
.scroll{overflow-x:auto}
.more{margin-top:12px;background:var(--cloud);border:1.5px solid var(--line);border-radius:9px;
padding:10px 16px;font:inherit;font-weight:700;color:var(--navy);cursor:pointer}
.more:hover{border-color:var(--em)}
.prose p,.prose ul{margin-bottom:14px;max-width:70ch;color:#22375c}
.prose ul{margin-left:20px}
.prose li{margin-bottom:7px}
.formula{background:var(--navy);color:#DCE5F3;border-radius:11px;padding:16px 18px;
font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:14px;overflow-x:auto;margin-bottom:14px}
.formula b{color:var(--em)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(232px,1fr));gap:14px}
.tile{background:#fff;border:1px solid var(--line);border-radius:12px;padding:18px}
.tile:hover{border-color:var(--em);text-decoration:none}
.tile b{display:block;font-size:16.5px;margin-bottom:5px}
.tile p{font-size:14px;color:var(--slate)}
.note{background:#FFF8EC;border:1px solid #F2DCB3;border-radius:11px;padding:15px 17px;font-size:14.5px;color:#6B4A12}
.faq details{background:#fff;border:1px solid var(--line);border-radius:11px;padding:15px 17px;margin-bottom:9px}
.faq summary{font-weight:700;cursor:pointer;list-style:none}
.faq summary::-webkit-details-marker{display:none}
.faq summary::after{content:"+";float:right;color:var(--em);font-weight:800}
.faq details[open] summary::after{content:"\\2212"}
.faq .a{margin-top:10px;color:#22375c;font-size:15px}
footer{background:#fff;border-top:1px solid var(--line);margin-top:34px;padding:28px 0;font-size:14px;color:var(--slate)}
.fnav{display:flex;gap:18px;flex-wrap:wrap;margin-bottom:12px}
.fnav a{color:var(--slate)}
"""


def shell(page):
    """Render one page. Everything inline - no external request is ever made."""
    parts = []
    if page["path"] != "/":
        parts.append({
            "@context": "https://schema.org", "@type": "BreadcrumbList",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": SITE + "/"},
                {"@type": "ListItem", "position": 2, "name": page["crumb"],
                 "item": SITE + page["path"]},
            ]})
    parts.extend(page.get("schema", []))
    ld = "".join('<script type="application/ld+json">%s</script>'
                 % json.dumps(s, separators=(",", ":")) for s in parts)

    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{site}{path}">
<meta property="og:type" content="website">
<meta property="og:url" content="{site}{path}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:site_name" content="{name}">
<meta name="twitter:card" content="summary">
<meta name="theme-color" content="{navy}">
<link rel="icon" href="{favicon}">
<style>{css}</style>
</head>
<body>
<header><div class="wrap hrow">
<a class="logo" href="/">{logo}Borrow<em>Calc</em></a>
<nav>
<a href="/mortgage-calculator/">Mortgage</a>
<a href="/auto-loan-calculator/">Auto Loan</a>
<a href="/personal-loan-calculator/">Personal Loan</a>
<a href="/about/">About</a>
</nav>
</div></header>
{body}
<footer><div class="wrap">
<div class="fnav">
<a href="/mortgage-calculator/">Mortgage Calculator</a>
<a href="/auto-loan-calculator/">Auto Loan Calculator</a>
<a href="/personal-loan-calculator/">Personal Loan Calculator</a>
<a href="/about/">About</a>
<a href="/privacy/">Privacy</a>
<a href="/contact/">Contact</a>
</div>
<p>&copy; {year} {name}. Estimates are for planning only and are not financial advice
or an offer of credit. Confirm all figures with a licensed lender.</p>
</div></footer>
{ld}
{js}
</body>
</html>""".format(title=page["title"], desc=page["desc"], site=SITE, path=page["path"],
                  name=NAME, navy=NAVY, favicon=FAVICON, css=CSS, logo=LOGO,
                  body=page["body"], year=YEAR, ld=ld, js=page.get("js", ""))


def write(path, content):
    d = OUT if path == "/" else OUT + path.rstrip("/")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "index.html"), "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return len(content.encode("utf-8"))


def write_raw(name, content):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="\n") as f:
        f.write(content)
    return len(content.encode("utf-8"))
