#!/usr/bin/env python3
"""Assemble and write the BorrowCalc site.

Run: python make.py   ->  dist/
"""
import os
import datetime
import build
import pages

SITE = build.SITE
TODAY = datetime.date.today().isoformat()

# ------------------------------------------------------ generic loan page ----
# Auto and personal loans are the same maths as a mortgage minus the escrow
# items, so one template drives both. Adding "student loan" or "credit card
# payoff" later is a dict, not a new file.
SIMPLE_JS = pages.ENGINE + """
function calc(){
  var P=num('amt'), rate=num('rate'), yrs=num('term'), down=num('down'), fees=num('fees');
  var principal=P-down+fees; if(principal<0)principal=0;
  var r=rate/12/100, n=Math.round(yrs*12);
  var m=pmt(principal,r,n);
  var rows=schedule(principal,r,n,m);
  var ti=rows.length?rows[rows.length-1].ti:0;
  document.getElementById('out').textContent=money2(m);
  document.getElementById('o-loan').textContent=money(principal);
  document.getElementById('o-int').textContent=money(ti);
  document.getElementById('o-cost').textContent=money(principal+ti);
  var tot=principal+ti;
  document.getElementById('bar').innerHTML=
    '<i style="width:'+(tot?principal/tot*100:0).toFixed(2)+'%;background:#0FA968"></i>'+
    '<i style="width:'+(tot?ti/tot*100:0).toFixed(2)+'%;background:#E0B341"></i>';
  var tb='',yi=0,yp=0,yr=0;
  for(var i=0;i<rows.length;i++){
    yi+=rows[i].int; yp+=rows[i].prin;
    if((i+1)%12===0||i===rows.length-1){
      yr++;
      tb+='<tr><td>'+yr+'</td><td>'+money(yp)+'</td><td>'+money(yi)+'</td><td>'+money(rows[i].bal)+'</td></tr>';
      yi=0;yp=0;
    }
  }
  document.getElementById('amort').innerHTML=tb;
}
document.addEventListener('input',function(e){if(e.target.closest('.fields'))calc();});
calc();
"""


def simple_body(cfg):
    return """
<div class="wrap hero">
<h1>{h1}</h1>
<p class="lead">{lead}</p>
</div>
<div class="wrap">
<div class="calc">
  <div class="card"><div class="fields">
    <div class="f"><label for="amt">{amt_label}</label>
      <div class="ip"><s>$</s><input id="amt" type="number" inputmode="decimal" value="{amt}" min="0" step="500"></div></div>
    <div class="two">
      <div class="f"><label for="down">Down payment / trade-in</label>
        <div class="ip"><s>$</s><input id="down" type="number" inputmode="decimal" value="{down}" min="0" step="500"></div></div>
      <div class="f"><label for="fees">Fees rolled in</label>
        <div class="ip"><s>$</s><input id="fees" type="number" inputmode="decimal" value="{fees}" min="0" step="100"></div></div>
    </div>
    <div class="two">
      <div class="f"><label for="rate">Interest rate <span class="hint">APR</span></label>
        <div class="ip"><input id="rate" type="number" inputmode="decimal" value="{rate}" min="0" max="60" step="0.01"><s>%</s></div></div>
      <div class="f"><label for="term">Term <span class="hint">years</span></label>
        <div class="ip"><input id="term" type="number" inputmode="numeric" value="{term}" min="1" max="30" step="1"><s>yr</s></div></div>
    </div>
  </div></div>
  <div class="res">
    <div class="cap">Monthly payment</div>
    <div class="big" id="out">$0</div>
    <div class="bar" id="bar"></div>
    <div class="key">
      <span><b style="background:#0FA968"></b>Principal</span>
      <span><b style="background:#E0B341"></b>Interest</span>
    </div>
    <div class="tot">
      <div><span>Amount financed</span><b id="o-loan">$0</b></div>
      <div><span>Total interest</span><b id="o-int">$0</b></div>
      <div><span>Total of payments</span><b id="o-cost">$0</b></div>
    </div>
  </div>
</div>
</div>
<section class="wrap">
  <h2>Amortisation schedule</h2>
  <div class="card"><div class="scroll"><table class="tbl">
  <thead><tr><th>Year</th><th>Principal paid</th><th>Interest paid</th><th>Balance</th></tr></thead>
  <tbody id="amort"></tbody></table></div></div>
</section>
<section class="wrap prose">
  <h2>How this is calculated</h2>
  <div class="formula">M = P &times; [ <b>r</b>(1 + <b>r</b>)<sup>n</sup> ] / [ (1 + <b>r</b>)<sup>n</sup> &minus; 1 ]</div>
  {body}
  <div class="note"><b>Worth knowing:</b> this is an estimate for planning, not a
  loan offer. Your actual rate depends on credit score, term and lender.</div>
</section>
<section class="wrap">
  <h2>Common questions</h2>
  <div class="faq">{faq}</div>
</section>
<section class="wrap">
  <h2>Other calculators</h2>
  <div class="grid">{tiles}</div>
</section>
""".format(**cfg)


def faq_html(items):
    out = []
    for i, (q, a) in enumerate(items):
        op = " open" if i == 0 else ""
        out.append('<details%s><summary>%s</summary><div class="a">%s</div></details>' % (op, q, a))
    return "".join(out)


def tiles(exclude):
    all_t = [
        ("/mortgage-calculator/", "Mortgage Calculator", "Full monthly payment including tax, insurance and PMI."),
        ("/auto-loan-calculator/", "Auto Loan Calculator", "Monthly payment and total interest on a car loan."),
        ("/personal-loan-calculator/", "Personal Loan Calculator", "Compare rates and terms on unsecured borrowing."),
    ]
    return "".join('<a class="tile" href="%s"><b>%s</b><p>%s</p></a>' % t
                   for t in all_t if t[0] != exclude)


def calc_schema(name, desc, path):
    return {"@context": "https://schema.org", "@type": "WebApplication",
            "name": name, "url": SITE + path, "description": desc,
            "applicationCategory": "FinanceApplication",
            "operatingSystem": "Any (web browser)",
            "browserRequirements": "Requires JavaScript",
            "offers": {"@type": "Offer", "price": "0", "priceCurrency": "USD"}}


# ------------------------------------------------------------------ pages ----
PAGES = []

PAGES.append({
    "path": "/mortgage-calculator/", "crumb": "Mortgage Calculator",
    "title": "Mortgage Calculator - Monthly Payment with Tax, Insurance & PMI | BorrowCalc",
    "desc": "Free mortgage calculator with property tax, home insurance, PMI and HOA. "
            "See your full monthly payment, total interest and a year-by-year amortisation schedule.",
    "body": pages.MORTGAGE_BODY,
    "js": "<script>%s</script>" % pages.MORTGAGE_JS,
    "schema": [calc_schema("Mortgage Calculator",
                           "Calculate a full monthly mortgage payment including principal, "
                           "interest, property tax, insurance and PMI.",
                           "/mortgage-calculator/")],
})

PAGES.append({
    "path": "/auto-loan-calculator/", "crumb": "Auto Loan Calculator",
    "title": "Auto Loan Calculator - Car Payment & Total Interest | BorrowCalc",
    "desc": "Free auto loan calculator. Work out your monthly car payment, total interest "
            "and full amortisation schedule, including trade-in and rolled-in fees.",
    "body": simple_body({
        "h1": "Auto Loan Calculator",
        "lead": "Work out your monthly car payment and see exactly how much interest "
                "the loan costs over its full term.",
        "amt_label": "Vehicle price", "amt": 35000, "down": 5000, "fees": 1200,
        "rate": 7.5, "term": 5,
        "body": "<p>A car loan amortises exactly like a mortgage: each payment covers the "
                "interest accrued that month, and whatever is left reduces the balance. "
                "Because vehicles depreciate faster than the loan amortises, a long term "
                "with little money down often leaves you owing more than the car is worth "
                "- negative equity.</p>"
                "<p>Fees rolled into the loan (documentation, registration, extended warranty) "
                "increase the amount financed, so you pay interest on them for the whole term. "
                "Paying those upfront instead usually saves more than people expect.</p>",
        "faq": faq_html([
            ("Should I take a longer term to lower the payment?",
             "It lowers the monthly figure but raises total interest, and stretches the period "
             "where you owe more than the car is worth. Compare the total interest line at "
             "5 years versus 7 - the monthly saving is usually small, the extra cost is not."),
            ("Does a trade-in work like a down payment?",
             "Yes. Its value reduces the amount financed exactly as cash would. Enter the "
             "trade-in value in the down payment field."),
            ("What about 0% finance offers?",
             "This calculator handles 0% correctly - set the rate to 0 and the payment becomes "
             "the amount financed divided by the number of months. Do check whether taking 0% "
             "means giving up a cash rebate; sometimes the rebate is worth more."),
            ("Is my data sent anywhere?",
             "No. Everything is calculated in your browser and nothing is transmitted or stored."),
        ]),
        "tiles": tiles("/auto-loan-calculator/"),
    }),
    "js": "<script>%s</script>" % SIMPLE_JS,
    "schema": [calc_schema("Auto Loan Calculator",
                           "Calculate monthly car payments and total interest.",
                           "/auto-loan-calculator/")],
})

PAGES.append({
    "path": "/personal-loan-calculator/", "crumb": "Personal Loan Calculator",
    "title": "Personal Loan Calculator - Monthly Payment & Interest | BorrowCalc",
    "desc": "Free personal loan calculator. See your monthly repayment, total interest cost "
            "and amortisation schedule for any loan amount, rate and term.",
    "body": simple_body({
        "h1": "Personal Loan Calculator",
        "lead": "See the monthly repayment and the true total cost of an unsecured "
                "personal loan before you sign.",
        "amt_label": "Loan amount", "amt": 15000, "down": 0, "fees": 0,
        "rate": 11.5, "term": 4,
        "body": "<p>Personal loans are unsecured, meaning no asset backs them. That makes "
                "rates higher than a mortgage or car loan and far more dependent on your "
                "credit score - the spread between the best and worst advertised rates is "
                "often more than twenty percentage points.</p>"
                "<p>Watch for origination fees. A loan advertised at one rate but charging a "
                "percentage upfront costs more than the headline suggests. Enter that fee in "
                "the fees field to see its real effect on what you repay.</p>",
        "faq": faq_html([
            ("What rate will I actually get?",
             "Advertised rates are usually the best available and go to borrowers with strong "
             "credit. Most lenders offer a soft-search pre-qualification that shows your real "
             "rate without affecting your credit score."),
            ("Is a personal loan cheaper than a credit card?",
             "Usually yes. Card APRs commonly sit well above personal loan rates, which is why "
             "consolidating card balances into a fixed-term loan can reduce both the rate and "
             "the time spent in debt - provided you stop adding to the cards."),
            ("Can I repay early?",
             "Most lenders allow it, and because interest is charged on the outstanding balance "
             "each month, paying early genuinely reduces total interest. Check for prepayment "
             "penalties before signing."),
            ("Is my data sent anywhere?",
             "No. Everything is calculated in your browser and nothing is transmitted or stored."),
        ]),
        "tiles": tiles("/personal-loan-calculator/"),
    }),
    "js": "<script>%s</script>" % SIMPLE_JS,
    "schema": [calc_schema("Personal Loan Calculator",
                           "Calculate personal loan repayments and total interest.",
                           "/personal-loan-calculator/")],
})

HOME_BODY = """
<div class="wrap hero">
<h1>Loan calculators that show the <em style="font-style:normal;color:#0FA968">whole</em> cost</h1>
<p class="lead">Free, fast and private. Every calculation runs in your browser - nothing you
type is ever sent to a server. No signup, no ads pretending to be results.</p>
</div>
<section class="wrap">
<div class="grid">
  <a class="tile" href="/mortgage-calculator/"><b>Mortgage Calculator</b>
    <p>Full monthly payment with property tax, insurance, PMI and HOA - plus a year-by-year amortisation schedule.</p></a>
  <a class="tile" href="/auto-loan-calculator/"><b>Auto Loan Calculator</b>
    <p>Car payment including trade-in and rolled-in fees, with the total interest the loan really costs.</p></a>
  <a class="tile" href="/personal-loan-calculator/"><b>Personal Loan Calculator</b>
    <p>Monthly repayment and true cost of unsecured borrowing, including origination fees.</p></a>
</div>
</section>
<section class="wrap prose">
  <h2>Why these calculators are different</h2>
  <p>Most loan calculators show you a principal-and-interest figure and stop there.
  That number is not what leaves your bank account. A mortgage payment also carries
  property tax, insurance and often PMI - together they can add thirty percent or
  more to the monthly cost, which is exactly the gap that catches first-time buyers
  out.</p>
  <p>Every calculator here shows the complete picture: the full monthly payment, how
  it splits, the total interest across the life of the loan, and a schedule of how
  the balance actually falls. The formula used is printed on each page so you can
  check the maths yourself.</p>
  <h2>Nothing you type leaves your device</h2>
  <p>These tools are plain HTML and JavaScript. There is no account, no tracking of
  your figures, and no server that ever sees your income, loan balance or property
  value. The page you are reading loaded without a single external request.</p>
</section>
"""

PAGES.append({
    "path": "/", "crumb": "Home",
    "title": "BorrowCalc - Free Mortgage, Auto & Personal Loan Calculators",
    "desc": "Free loan calculators showing your full monthly payment and total interest. "
            "Mortgage with tax, insurance and PMI, auto loans and personal loans. "
            "Private - everything runs in your browser.",
    "body": HOME_BODY,
    "schema": [
        {"@context": "https://schema.org", "@type": "WebSite", "name": build.NAME,
         "url": SITE + "/",
         "description": "Free mortgage, auto and personal loan calculators."},
        {"@context": "https://schema.org", "@type": "Organization", "name": build.NAME,
         "url": SITE + "/", "logo": SITE + "/logo.svg"},
    ],
})

# Trust pages. For a finance site these are not optional - Google holds
# money-related content to a higher bar, and a missing contact or about page is
# a common reason such sites fail to gain traction.
PAGES.append({
    "path": "/about/", "crumb": "About",
    "title": "About BorrowCalc - How We Calculate and Why",
    "desc": "Who runs BorrowCalc, how the loan formulas work, and why every calculation "
            "happens in your browser instead of on a server.",
    "body": """
<div class="wrap hero"><h1>About BorrowCalc</h1>
<p class="lead">Straightforward loan maths, shown in full, with nothing hidden and nothing collected.</p></div>
<section class="wrap prose">
<h2>What this site does</h2>
<p>BorrowCalc provides free calculators for the borrowing decisions most people
face: a mortgage, a car loan, a personal loan. Each one shows the complete monthly
cost and the total interest paid over the life of the loan, not just the headline
principal-and-interest figure.</p>
<h2>How the numbers are produced</h2>
<p>Every calculator uses the standard amortising-loan formula that lenders
themselves use. It is printed on each calculator page so you can verify it. The
amortisation schedule is computed month by month, charging interest on the balance
actually remaining, rather than approximating with an average.</p>
<div class="formula">M = P &times; [ <b>r</b>(1 + <b>r</b>)<sup>n</sup> ] / [ (1 + <b>r</b>)<sup>n</sup> &minus; 1 ]</div>
<h2>Your privacy</h2>
<p>The calculators are plain JavaScript running in your browser. Your home price,
income, loan balance and rate are never transmitted anywhere, because there is no
server-side calculation to send them to. Close the tab and the figures are gone.</p>
<h2>What we are not</h2>
<p>BorrowCalc is not a lender, a broker, or a financial adviser, and we are not paid
to route you to any lender. The figures here are estimates for planning. Your real
rate depends on your credit, the lender and the loan type, and a real quote will
include costs - origination fees, points, closing costs - that no monthly payment
figure can capture. Always confirm with a licensed lender before committing.</p>
<h2>Corrections</h2>
<p>If you believe a calculation is wrong, please tell us. Accuracy matters more to us
than anything else on this site, and we would rather fix an error than defend it.
Reach us via the <a href="/contact/">contact page</a>.</p>
</section>""",
})

PAGES.append({
    "path": "/privacy/", "crumb": "Privacy",
    "title": "Privacy Policy | BorrowCalc",
    "desc": "How BorrowCalc handles data. Calculations run in your browser and your "
            "financial figures are never transmitted or stored.",
    "body": """
<div class="wrap hero"><h1>Privacy Policy</h1>
<p class="lead">Short version: your numbers stay on your device.</p></div>
<section class="wrap prose">
<h2>What we collect</h2>
<p>We do not collect, transmit or store the figures you enter into any calculator on
this site. All calculations run locally in your browser using JavaScript. There is no
account system and no submission of your data to any server.</p>
<h2>Analytics</h2>
<p>We may use privacy-respecting analytics to count page views and understand which
calculators are used. This does not capture the values you type.</p>
<h2>Advertising</h2>
<p>This site may display advertising. Advertising partners may use cookies to measure
performance and show relevant ads. Where required by law, you will be asked for consent
before any non-essential cookie is set, and you can change or withdraw that choice at
any time.</p>
<h2>Your rights</h2>
<p>If you are in the EU, UK or a jurisdiction with comparable law, you have the right to
access, correct and erase personal data held about you, and to object to processing.
Because we do not store your calculator inputs, there is generally nothing of that kind
to retrieve - but you can contact us with any request.</p>
<h2>Contact</h2>
<p>Questions about this policy can be sent via the <a href="/contact/">contact page</a>.</p>
</section>""",
})

PAGES.append({
    "path": "/contact/", "crumb": "Contact",
    "title": "Contact BorrowCalc",
    "desc": "Get in touch with BorrowCalc about a calculation error, a correction, "
            "a feature request or a press enquiry.",
    "body": """
<div class="wrap hero"><h1>Contact</h1>
<p class="lead">Corrections especially welcome - accuracy is the point of this site.</p></div>
<section class="wrap prose">
<h2>Email</h2>
<p><b>hello@borrowcalc.com</b></p>
<p>We aim to reply within a couple of business days.</p>
<h2>Reporting a calculation error</h2>
<p>If a figure looks wrong, please include the exact inputs you used - loan amount,
rate, term and any extras - along with the result you expected. That lets us reproduce
it immediately. Loan maths is unforgiving, and we would rather hear about a mistake
than have it sit there.</p>
<h2>What we cannot help with</h2>
<p>We are not a lender or a broker, so we cannot approve applications, quote you a
real rate, or advise on which product to choose. For that, speak to a licensed lender
or a regulated financial adviser.</p>
</section>""",
})


def main():
    total = 0
    print("building %s\n" % SITE)
    for p in PAGES:
        n = build.write(p["path"], build.shell(p))
        total += n
        print("  %-34s %6.1f KB" % (p["path"], n / 1024.0))

    # robots.txt - AI search crawlers are explicitly allowed. As of 2026 these
    # bots govern citability in AI answers (a real and growing traffic source),
    # and they are distinct from the training crawlers.
    robots = """User-agent: *
Allow: /

# AI search crawlers - allowed: these control citability in AI answers.
User-agent: OAI-SearchBot
Allow: /
User-agent: Claude-SearchBot
Allow: /
User-agent: PerplexityBot
Allow: /

Sitemap: %s/sitemap.xml
""" % SITE
    total += build.write_raw("robots.txt", robots)

    urls = []
    for p in PAGES:
        pri = "1.0" if p["path"] == "/" else ("0.9" if "calculator" in p["path"] else "0.4")
        freq = "weekly" if "calculator" in p["path"] or p["path"] == "/" else "yearly"
        urls.append("  <url><loc>%s%s</loc><lastmod>%s</lastmod>"
                    "<changefreq>%s</changefreq><priority>%s</priority></url>"
                    % (SITE, p["path"], TODAY, freq, pri))
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + "\n".join(urls) + "\n</urlset>\n")
    total += build.write_raw("sitemap.xml", sitemap)

    # Standalone logo for schema/social references.
    logo_svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
                + build.LOGO.split(">", 1)[1])
    total += build.write_raw("logo.svg", logo_svg)

    print("\n  robots.txt, sitemap.xml, logo.svg")
    print("\n  %d pages, %.1f KB total" % (len(PAGES), total / 1024.0))
    print("  output: %s" % build.OUT)


if __name__ == "__main__":
    main()
