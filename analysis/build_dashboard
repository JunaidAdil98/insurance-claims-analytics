"""build_dashboard.py — reads docs/dashboard_data.json, writes a self-contained docs/index.html."""
import json

with open("docs/dashboard_data.json") as f:
    data = json.load(f)

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Auto Claims Analytics — Portfolio Review</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,900&family=Libre+Franklin:wght@400;500;600;700&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  :root{
    --paper:#F6F3EC; --ink:#15233B; --ink2:#46566F; --line:#E1DACB;
    --amber:#D8842A; --teal:#2F6E6A; --red:#B4452F; --card:#FFFEFB;
    --shadow:0 1px 2px rgba(21,35,59,.06),0 8px 24px rgba(21,35,59,.06);
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--paper);color:var(--ink);font-family:'Libre Franklin',sans-serif;
    line-height:1.5;-webkit-font-smoothing:antialiased;
    background-image:radial-gradient(circle at 12% -5%,rgba(216,132,42,.07),transparent 38%),
                     radial-gradient(circle at 95% 0%,rgba(47,110,106,.07),transparent 42%);}
  .wrap{max-width:1180px;margin:0 auto;padding:48px 28px 72px}
  header{border-bottom:2px solid var(--ink);padding-bottom:22px;margin-bottom:8px;
    display:flex;justify-content:space-between;align-items:flex-end;gap:24px;flex-wrap:wrap}
  .eyebrow{font:600 12px/1 'JetBrains Mono',monospace;letter-spacing:.22em;text-transform:uppercase;color:var(--amber);margin-bottom:14px}
  h1{font-family:'Fraunces',serif;font-weight:900;font-size:clamp(30px,4.4vw,50px);line-height:1.02;letter-spacing:-.015em}
  h1 em{font-style:italic;font-weight:400;color:var(--teal)}
  .sub{color:var(--ink2);max-width:560px;margin-top:12px;font-size:15px}
  .badge{font:500 11px/1.4 'JetBrains Mono',monospace;color:var(--ink2);border:1px solid var(--line);
    background:var(--card);border-radius:999px;padding:7px 13px;white-space:nowrap}
  .kpis{display:grid;grid-template-columns:repeat(6,1fr);gap:14px;margin:32px 0 10px}
  .kpi{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:16px 16px 18px;box-shadow:var(--shadow);
    opacity:0;transform:translateY(10px);animation:rise .6s forwards}
  .kpi .lab{font:600 10.5px/1.2 'JetBrains Mono',monospace;letter-spacing:.1em;text-transform:uppercase;color:var(--ink2)}
  .kpi .val{font-family:'Fraunces',serif;font-weight:600;font-size:28px;margin-top:10px;letter-spacing:-.01em}
  .kpi.flag .val{color:var(--red)}
  .kpi .note{font-size:11.5px;color:var(--ink2);margin-top:3px}
  .grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-top:22px}
  .card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:22px 22px 18px;box-shadow:var(--shadow);
    opacity:0;transform:translateY(10px);animation:rise .7s forwards}
  .card.wide{grid-column:1 / -1}
  .card h3{font-family:'Fraunces',serif;font-size:19px;font-weight:600;letter-spacing:-.01em}
  .card p.cap{color:var(--ink2);font-size:13px;margin-top:4px;margin-bottom:14px}
  .chartbox{position:relative;height:280px}
  .chartbox.tall{height:330px}
  .insight{margin-top:14px;font-size:13px;color:var(--ink);background:rgba(47,110,106,.07);
    border-left:3px solid var(--teal);padding:10px 13px;border-radius:0 8px 8px 0}
  .insight b{color:var(--teal)}
  footer{margin-top:40px;border-top:1px solid var(--line);padding-top:20px;color:var(--ink2);font-size:12.5px;line-height:1.7}
  footer code{font-family:'JetBrains Mono',monospace;background:#ece6d8;padding:1px 6px;border-radius:5px;font-size:11.5px}
  @keyframes rise{to{opacity:1;transform:none}}
  .kpi:nth-child(1){animation-delay:.04s}.kpi:nth-child(2){animation-delay:.09s}.kpi:nth-child(3){animation-delay:.14s}
  .kpi:nth-child(4){animation-delay:.19s}.kpi:nth-child(5){animation-delay:.24s}.kpi:nth-child(6){animation-delay:.29s}
  @media(max-width:880px){.kpis{grid-template-columns:repeat(2,1fr)}.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div>
      <div class="eyebrow">Claims Portfolio Review · FY21–FY24</div>
      <h1>Auto Insurance <em>Loss Analytics</em></h1>
      <p class="sub">Diagnosing why the book is running unprofitably: where losses concentrate, what drives claim cost and frequency, and how recent accident years are developing.</p>
    </div>
    <div class="badge">Simulated dataset · methodology mirrors real AMI/claims data</div>
  </header>

  <section class="kpis" id="kpis"></section>

  <div class="grid">
    <div class="card">
      <h3>Loss ratio by region</h3>
      <p class="cap">Incurred losses ÷ earned premium. The break-even line is 100%.</p>
      <div class="chartbox"><canvas id="lrRegion"></canvas></div>
      <div class="insight" id="ins-region"></div>
    </div>
    <div class="card">
      <h3>Loss ratio by coverage</h3>
      <p class="cap">Which products are underpriced for the risk they carry.</p>
      <div class="chartbox"><canvas id="lrCov"></canvas></div>
    </div>
    <div class="card">
      <h3>Claim frequency by driver age</h3>
      <p class="cap">Claims per policy. Younger drivers file more often.</p>
      <div class="chartbox"><canvas id="freqAge"></canvas></div>
    </div>
    <div class="card">
      <h3>Average severity by claim type</h3>
      <p class="cap">Mean incurred cost per claim, by cause of loss.</p>
      <div class="chartbox"><canvas id="sevType"></canvas></div>
    </div>
    <div class="card wide">
      <h3>Accident-year loss development</h3>
      <p class="cap">Cohort analysis: share of ultimate losses paid at each development age. Recent years are immature — useful for reserving.</p>
      <div class="chartbox tall"><canvas id="devCurve"></canvas></div>
      <div class="insight" id="ins-dev"></div>
    </div>
    <div class="card">
      <h3>Severity drivers (regression)</h3>
      <p class="cap">% effect on claim cost, log-linear model · R² = <span id="r2"></span></p>
      <div class="chartbox"><canvas id="sevModel"></canvas></div>
    </div>
    <div class="card">
      <h3>Frequency drivers (logistic)</h3>
      <p class="cap">Odds ratio of filing a claim · AUC = <span id="auc"></span> · >1 raises risk</p>
      <div class="chartbox"><canvas id="freqModel"></canvas></div>
    </div>
  </div>

  <footer>
    <b>Stack:</b> Python (pandas, scikit-learn) for the pipeline · T-SQL for warehouse queries · Chart.js for the dashboard · static hosting on GitHub Pages.<br>
    <b>Methods:</b> descriptive KPIs · diagnostic segmentation · accident-year cohort loss development · log-linear severity regression · logistic frequency model.<br>
    <b>Note:</b> data is synthetic and generated by <code>generate_data.py</code>; every figure above is the real output of <code>analysis.py</code> run on it. The methodology transfers directly to production claims data.
  </footer>
</div>

<script>
const DATA = __DATA__;
const INK='#15233B', INK2='#46566F', AMBER='#D8842A', TEAL='#2F6E6A', RED='#B4452F', LINE='#E1DACB';
Chart.defaults.font.family="'Libre Franklin',sans-serif";
Chart.defaults.font.size=12; Chart.defaults.color=INK2;
const money=v=>'$'+Math.round(v).toLocaleString();
const pct=v=>(v*100).toFixed(1)+'%';

/* KPI cards */
const k=DATA.kpis;
const cards=[
  ['Loss ratio',pct(k.loss_ratio),'break-even = 100%',k.loss_ratio>1],
  ['Claims',k.claims.toLocaleString(),pct(k.frequency)+' frequency',false],
  ['Avg severity',money(k.avg_severity),'per claim',false],
  ['Earned premium',money(k.earned_premium),'FY21–24',false],
  ['Incurred losses',money(k.incurred),pct(k.paid/k.incurred)+' paid',false],
  ['Open claims',k.open_claims.toLocaleString(),pct(k.open_share)+' of total',false],
];
document.getElementById('kpis').innerHTML=cards.map(c=>
  `<div class="kpi${c[3]?' flag':''}"><div class="lab">${c[0]}</div><div class="val">${c[1]}</div><div class="note">${c[2]}</div></div>`).join('');

const grid={grid:{color:'rgba(21,35,59,.06)'},border:{display:false}};
const noGrid={grid:{display:false},border:{display:false}};
const baseOpts=(extra={})=>Object.assign({responsive:true,maintainAspectRatio:false,
  plugins:{legend:{display:false}}},extra);

/* loss ratio by region */
const reg=DATA.loss_ratio_by_region;
new Chart(lrRegion,{type:'bar',data:{labels:reg.map(d=>d.region),
  datasets:[{data:reg.map(d=>d.loss_ratio),
    backgroundColor:reg.map(d=>d.loss_ratio>=1?RED:d.loss_ratio>=.9?AMBER:TEAL),borderRadius:6}]},
  options:baseOpts({indexAxis:'y',scales:{x:Object.assign({ticks:{callback:v=>(v*100)+'%'}},grid),y:noGrid},
    plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>'Loss ratio '+pct(c.raw)}}}})});
document.getElementById('ins-region').innerHTML=
  `<b>${reg[0].region}</b> is the worst book at ${pct(reg[0].loss_ratio)} — losses exceed premium. Repricing or tightening underwriting here is the highest-impact lever.`;

/* loss ratio by coverage */
const cov=DATA.loss_ratio_by_coverage;
new Chart(lrCov,{type:'bar',data:{labels:cov.map(d=>d.coverage),
  datasets:[{data:cov.map(d=>d.loss_ratio),backgroundColor:cov.map(d=>d.loss_ratio>=1?RED:d.loss_ratio>=.9?AMBER:TEAL),borderRadius:6}]},
  options:baseOpts({scales:{y:Object.assign({ticks:{callback:v=>(v*100)+'%'}},grid),x:noGrid},
    plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>pct(c.raw)}}}})});

/* frequency by age */
const fa=DATA.frequency_by_age;
new Chart(freqAge,{type:'bar',data:{labels:fa.map(d=>d.age_band),
  datasets:[{data:fa.map(d=>d.frequency),backgroundColor:fa.map((d,i)=>i===0?AMBER:'#9DB0AE'),borderRadius:6}]},
  options:baseOpts({scales:{y:Object.assign({ticks:{callback:v=>(v*100).toFixed(0)+'%'}},grid),x:noGrid},
    plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>pct(c.raw)+' claims/policy'}}}})});

/* severity by type */
const st=DATA.severity_by_type;
new Chart(sevType,{type:'bar',data:{labels:st.map(d=>d.claim_type),
  datasets:[{data:st.map(d=>d.avg_severity),backgroundColor:TEAL,borderRadius:6}]},
  options:baseOpts({scales:{y:Object.assign({ticks:{callback:v=>'$'+(v/1000)+'k'}},grid),x:noGrid},
    plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>money(c.raw)+' avg'}}}})});

/* loss development */
const dev=DATA.loss_development; const years=Object.keys(dev.cohorts);
const palette=[INK,TEAL,AMBER,RED];
new Chart(devCurve,{type:'line',data:{labels:dev.dev_ages.map(d=>d+'mo'),
  datasets:years.map((y,i)=>({label:y,data:dev.cohorts[y].map(v=>v*100),
    borderColor:palette[i%4],backgroundColor:'transparent',tension:.35,borderWidth:2.5,
    pointRadius:3,pointBackgroundColor:palette[i%4]}))},
  options:baseOpts({interaction:{mode:'index',intersect:false},
    scales:{y:Object.assign({ticks:{callback:v=>v+'%'},title:{display:true,text:'% of ultimate paid'}},grid),x:noGrid},
    plugins:{legend:{display:true,position:'bottom',labels:{usePointStyle:true,boxWidth:7,padding:16}},
      tooltip:{callbacks:{label:c=>'AY'+c.dataset.label+': '+c.raw.toFixed(0)+'% paid'}}}})});
const last=dev.cohorts[years[years.length-1]];
document.getElementById('ins-dev').innerHTML=
  `Accident year <b>${years[years.length-1]}</b> is only <b>${last[last.length-1].toFixed(0)}% developed</b> — open claims mean ultimate losses will rise, which matters for reserving.`;

/* severity model */
const sm=DATA.severity_model; document.getElementById('r2').textContent=sm.r2;
new Chart(sevModel,{type:'bar',data:{labels:sm.drivers.map(d=>d.feature.replace(/_/g,' ')),
  datasets:[{data:sm.drivers.map(d=>d.pct_effect),backgroundColor:sm.drivers.map(d=>d.pct_effect>=0?RED:TEAL),borderRadius:5}]},
  options:baseOpts({indexAxis:'y',scales:{x:Object.assign({ticks:{callback:v=>v+'%'}},grid),y:noGrid},
    plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>(c.raw>0?'+':'')+c.raw+'% on severity'}}}})});

/* frequency model */
const fm=DATA.frequency_model; document.getElementById('auc').textContent=fm.auc;
new Chart(freqModel,{type:'bar',data:{labels:fm.drivers.map(d=>d.feature.replace(/_/g,' ')),
  datasets:[{data:fm.drivers.map(d=>d.odds_ratio),backgroundColor:fm.drivers.map(d=>d.odds_ratio>=1?RED:TEAL),borderRadius:5}]},
  options:baseOpts({indexAxis:'y',scales:{x:Object.assign({suggestedMin:.6,suggestedMax:1.3,ticks:{callback:v=>v+'x'}},grid),y:noGrid},
    plugins:{legend:{display:false},tooltip:{callbacks:{label:c=>'odds x'+c.raw}}}})});
</script>
</body>
</html>
"""

html = HTML.replace("__DATA__", json.dumps(data))
with open("docs/index.html", "w") as f:
    f.write(html)
print("wrote docs/index.html (", len(html), "bytes )")
