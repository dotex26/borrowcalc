#!/usr/bin/env python3
"""Page definitions for BorrowCalc.

Each page is a dict consumed by build.shell(). Calculator logic lives in the
JS block attached to its page - it runs client-side so results are instant and
no request leaves the browser. That is both a speed decision and a privacy one:
nobody's salary or loan balance is ever transmitted anywhere.
"""

# ---------------------------------------------------------------- engine ----
# Standard amortising-loan maths, shared by every calculator on the site.
#
#   M = P * [ r(1+r)^n ] / [ (1+r)^n - 1 ]
#
#   M = monthly principal + interest
#   P = principal (amount borrowed)
#   r = monthly rate = APR / 12 / 100
#   n = number of monthly payments = years * 12
#
# The r == 0 branch matters: a 0% promotional auto loan divides by zero in the
# formula above, and simple division is the correct limit as r approaches 0.
ENGINE = """
function pmt(P,r,n){if(!(P>0)||!(n>0))return 0;if(r===0)return P/n;
var g=Math.pow(1+r,n);return P*r*g/(g-1);}
function num(id){var e=document.getElementById(id);if(!e)return 0;
var v=parseFloat(String(e.value).replace(/[^0-9.\\-]/g,''));return isFinite(v)?v:0;}
// Build the full month-by-month schedule. Interest is charged on the balance
// remaining at the start of each month, so it must be recomputed every period
// rather than derived from a closed form.
function schedule(P,r,n,pay){
  var rows=[],bal=P,ti=0;
  for(var i=1;i<=n;i++){
    var int=bal*r, prin=pay-int;
    if(prin>bal)prin=bal;          // final payment: never overshoot
    bal-=prin; ti+=int;
    rows.push({m:i,int:int,prin:prin,bal:bal>0?bal:0,ti:ti});
    if(bal<=0)break;
  }
  return rows;
}
"""

MORTGAGE_JS = ENGINE + """
function calc(){
  var price=num('price'), dpPct=num('dppct'), rate=num('rate'), yrs=num('term'),
      taxPct=num('tax'), insY=num('ins'), pmiPct=num('pmi'), hoaM=num('hoa');
  var down=price*dpPct/100, P=price-down;
  if(P<0)P=0;
  var r=rate/12/100, n=Math.round(yrs*12);
  var pi=pmt(P,r,n);
  var taxM=price*taxPct/100/12, insM=insY/12;
  // PMI is conventionally dropped once equity reaches 20%, so a down payment
  // of 20% or more zeroes it regardless of what the field says.
  var pmiM=(dpPct<20)?(P*pmiPct/100/12):0;
  var total=pi+taxM+insM+pmiM+hoaM;

  document.getElementById('out').textContent=money(total);
  document.getElementById('o-pi').textContent=money(pi);
  document.getElementById('o-tax').textContent=money(taxM);
  document.getElementById('o-ins').textContent=money(insM);
  document.getElementById('o-pmi').textContent=money(pmiM);
  document.getElementById('o-hoa').textContent=money(hoaM);
  document.getElementById('o-loan').textContent=money(P);
  document.getElementById('o-down').textContent=money(down);

  var rows=schedule(P,r,n,pi);
  var ti=rows.length?rows[rows.length-1].ti:0;
  document.getElementById('o-int').textContent=money(ti);
  document.getElementById('o-cost').textContent=money(P+ti);

  var pmiRow=document.getElementById('r-pmi');
  if(pmiRow)pmiRow.style.display=pmiM>0?'flex':'none';

  // Payment-composition bar.
  var seg=[[pi,'#0FA968'],[taxM,'#4C82C3'],[insM,'#9DB2D4'],[pmiM,'#E0B341'],[hoaM,'#7A8CA8']];
  var bar='';
  for(var i=0;i<seg.length;i++){
    var w=total>0?(seg[i][0]/total*100):0;
    if(w>0)bar+='<i style="width:'+w.toFixed(2)+'%;background:'+seg[i][1]+'"></i>';
  }
  document.getElementById('bar').innerHTML=bar;

  // Yearly amortisation summary.
  var tb='',shown=0,yr=0,yi=0,yp=0;
  for(var i=0;i<rows.length;i++){
    yi+=rows[i].int; yp+=rows[i].prin;
    if((i+1)%12===0||i===rows.length-1){
      yr++;
      tb+='<tr><td>'+yr+'</td><td>'+money(yp)+'</td><td>'+money(yi)+'</td><td>'+
          money(rows[i].bal)+'</td></tr>';
      yi=0;yp=0;shown++;
      if(shown>=(window._full?999:10))break;
    }
  }
  document.getElementById('amort').innerHTML=tb;
  var btn=document.getElementById('moreBtn');
  if(btn)btn.style.display=(rows.length>120&&!window._full)?'inline-block':'none';
}
function showAll(){window._full=true;calc();}
// Recalculate on any input change; also run once immediately so the page never
// renders an empty result (which would cause a layout shift).
document.addEventListener('input',function(e){
  if(e.target.closest('.fields'))calc();
});
calc();
"""

MORTGAGE_BODY = """
<div class="wrap hero">
<h1>Mortgage Calculator</h1>
<p class="lead">Estimate your full monthly payment - principal, interest, property tax,
insurance, PMI and HOA - and see exactly how much interest you pay over the life of the loan.</p>
</div>

<div class="wrap">
<div class="calc">
  <div class="card">
    <div class="fields">
      <div class="f"><label for="price">Home price</label>
        <div class="ip"><s class="cs">$</s><input id="price" type="number" inputmode="decimal" value="400000" min="0" step="1000"></div></div>
      <div class="two">
        <div class="f"><label for="dppct">Down payment <span class="hint">%</span></label>
          <div class="ip"><input id="dppct" type="number" inputmode="decimal" value="20" min="0" max="100" step="0.5"><s>%</s></div></div>
        <div class="f"><label for="rate">Interest rate <span class="hint">APR</span></label>
          <div class="ip"><input id="rate" type="number" inputmode="decimal" value="6.5" min="0" max="30" step="0.01"><s>%</s></div></div>
      </div>
      <div class="f"><label for="term">Loan term <span class="hint">years</span></label>
        <div class="ip"><input id="term" type="number" inputmode="numeric" value="30" min="1" max="50" step="1"><s>yr</s></div></div>
      <div class="two">
        <div class="f"><label for="tax">Property tax <span class="hint">% / year</span></label>
          <div class="ip"><input id="tax" type="number" inputmode="decimal" value="1.1" min="0" step="0.01"><s>%</s></div></div>
        <div class="f"><label for="ins">Home insurance <span class="hint">$ / year</span></label>
          <div class="ip"><s class="cs">$</s><input id="ins" type="number" inputmode="decimal" value="1800" min="0" step="50"></div></div>
      </div>
      <div class="two">
        <div class="f"><label for="pmi">PMI <span class="hint">% / year</span></label>
          <div class="ip"><input id="pmi" type="number" inputmode="decimal" value="0.5" min="0" step="0.05"><s>%</s></div></div>
        <div class="f"><label for="hoa">HOA <span class="hint">$ / month</span></label>
          <div class="ip"><s class="cs">$</s><input id="hoa" type="number" inputmode="decimal" value="0" min="0" step="10"></div></div>
      </div>
    </div>
  </div>

  <div class="res">
    <div class="cap">Estimated monthly payment</div>
    <div class="big" id="out">$0</div>
    <div class="bar" id="bar"></div>
    <div class="key">
      <span><b style="background:#0FA968"></b>Principal &amp; interest</span>
      <span><b style="background:#4C82C3"></b>Tax</span>
      <span><b style="background:#9DB2D4"></b>Insurance</span>
      <span><b style="background:#E0B341"></b>PMI</span>
    </div>
    <div class="bd">
      <div><span>Principal &amp; interest</span><b id="o-pi">$0</b></div>
      <div><span>Property tax</span><b id="o-tax">$0</b></div>
      <div><span>Home insurance</span><b id="o-ins">$0</b></div>
      <div id="r-pmi"><span>PMI</span><b id="o-pmi">$0</b></div>
      <div><span>HOA</span><b id="o-hoa">$0</b></div>
    </div>
    <div class="tot">
      <div><span>Down payment</span><b id="o-down">$0</b></div>
      <div><span>Loan amount</span><b id="o-loan">$0</b></div>
      <div><span>Total interest paid</span><b id="o-int">$0</b></div>
      <div><span>Total of payments</span><b id="o-cost">$0</b></div>
    </div>
  </div>
</div>
</div>

<section class="wrap">
  <h2>Amortisation schedule</h2>
  <div class="card">
    <div class="scroll">
      <table class="tbl">
        <thead><tr><th>Year</th><th>Principal paid</th><th>Interest paid</th><th>Balance</th></tr></thead>
        <tbody id="amort"></tbody>
      </table>
    </div>
    <button class="more" id="moreBtn" onclick="showAll()">Show all years</button>
  </div>
</section>

<section class="wrap prose">
  <h2>How the payment is calculated</h2>
  <p>Your principal and interest payment comes from the standard amortising-loan
  formula. Every lender uses the same one, so the figure above should match a
  lender quote for the same inputs:</p>
  <div class="formula">M = P &times; [ <b>r</b>(1 + <b>r</b>)<sup>n</sup> ] / [ (1 + <b>r</b>)<sup>n</sup> &minus; 1 ]<br><br>
  M = monthly principal &amp; interest<br>
  P = principal (home price &minus; down payment)<br>
  r = monthly rate (APR &divide; 12 &divide; 100)<br>
  n = total payments (years &times; 12)</div>
  <p>The remaining pieces are added on top to reach the figure most people
  actually care about, the full monthly housing cost sometimes called PITI:</p>
  <ul>
    <li><b>Property tax</b> - an annual percentage of the home's assessed value, divided by 12. Rates vary enormously by state and county.</li>
    <li><b>Home insurance</b> - your annual premium divided by 12.</li>
    <li><b>PMI</b> - private mortgage insurance, normally required when your down payment is under 20%. This calculator drops it automatically at 20% or above.</li>
    <li><b>HOA</b> - homeowners association dues, if the property has them.</li>
  </ul>
  <p>Interest is charged on the balance remaining at the start of each month.
  Early on, most of your payment goes to interest and very little to principal -
  which is why the balance in the table above falls so slowly in the first years
  and then accelerates. The schedule recalculates the split every single month
  rather than estimating it.</p>

  <div class="note"><b>Worth knowing:</b> this is an estimate for planning, not a
  loan offer. Lenders may also charge origination fees, points, escrow set-up and
  closing costs, none of which appear in a monthly payment figure. Your actual
  rate depends on credit score, loan type and the lender.</div>
</section>

<section class="wrap">
  <h2>Common questions</h2>
  <div class="faq">
    <details open><summary>How much house can I afford?</summary><div class="a">A widely used guideline is that total housing costs stay at or below 28% of gross monthly income, and all debt payments below 36%. On a $6,000 monthly income that is roughly $1,680 of housing. Enter different home prices above until the monthly figure fits your budget.</div></details>
    <details><summary>Should I choose a 15-year or 30-year mortgage?</summary><div class="a">A 15-year loan has a higher monthly payment but dramatically less total interest, because you are borrowing for half the time and usually at a lower rate. Set the term field to 15 and compare the "total interest paid" line - the difference is often six figures.</div></details>
    <details><summary>When does PMI go away?</summary><div class="a">PMI is generally required until you hold 20% equity. Under US federal rules it must be cancelled automatically at 78% loan-to-value on the original schedule, and you can usually request cancellation at 80%. Rules differ for FHA loans, where the premium may last the life of the loan.</div></details>
    <details><summary>Does a bigger down payment save money?</summary><div class="a">Yes, in three ways at once: you borrow less, you pay interest on a smaller balance for the whole term, and at 20% you stop paying PMI entirely. Try changing the down payment from 10% to 20% and watch the total interest line.</div></details>
    <details><summary>What is not included in this estimate?</summary><div class="a">Closing costs, origination fees, discount points, escrow deposits, utilities and maintenance. Budget for maintenance separately - a common rule of thumb is around 1% of the home's value each year.</div></details>
    <details><summary>Is my data sent anywhere?</summary><div class="a">No. Every calculation runs in your browser. Nothing you type is transmitted to us or to anyone else, and nothing is stored.</div></details>
  </div>
</section>

<section class="wrap">
  <h2>Other calculators</h2>
  <div class="grid">
    <a class="tile" href="/auto-loan-calculator/"><b>Auto Loan Calculator</b><p>Monthly payment and total interest on a car loan.</p></a>
    <a class="tile" href="/personal-loan-calculator/"><b>Personal Loan Calculator</b><p>Compare rates and terms on unsecured borrowing.</p></a>
    <a class="tile" href="/"><b>All calculators</b><p>Every BorrowCalc tool in one place.</p></a>
  </div>
</section>
"""
