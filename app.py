"""
FNOL Agent Web UI - Flask application  (regex mode, no API key needed)
Run: python app.py  -> visit http://localhost:5000
"""

from flask import Flask, render_template_string, request, jsonify
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))
from agent import process_fnol

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FNOL Agent — Claims Processor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0c10;
    --surface: #111318;
    --surface2: #181b22;
    --border: #252830;
    --accent: #f0a500;
    --accent2: #ff6b35;
    --text: #e8eaf0;
    --muted: #6b7280;
    --green: #22c55e;
    --red: #ef4444;
    --blue: #3b82f6;
    --purple: #a855f7;
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { background:var(--bg); color:var(--text); font-family:'DM Sans',sans-serif; min-height:100vh; overflow-x:hidden; }
  body::before {
    content:''; position:fixed; inset:0;
    background-image: linear-gradient(rgba(240,165,0,.03) 1px,transparent 1px), linear-gradient(90deg,rgba(240,165,0,.03) 1px,transparent 1px);
    background-size:40px 40px; pointer-events:none; z-index:0;
  }
  header { position:relative; z-index:1; padding:1.5rem 2.5rem; border-bottom:1px solid var(--border); display:flex; align-items:center; gap:1.5rem; background:rgba(10,12,16,.8); backdrop-filter:blur(12px); }
  .logo-mark { width:44px; height:44px; background:linear-gradient(135deg,var(--accent),var(--accent2)); border-radius:10px; display:flex; align-items:center; justify-content:center; font-size:1.2rem; font-weight:800; color:#000; font-family:'Syne',sans-serif; flex-shrink:0; }
  header h1 { font-family:'Syne',sans-serif; font-size:1.35rem; font-weight:700; letter-spacing:-.02em; }
  header h1 span { color:var(--accent); }
  header p { color:var(--muted); font-size:.82rem; margin-top:2px; }
  .badge-nokey { padding:.2rem .6rem; background:rgba(34,197,94,.12); border:1px solid rgba(34,197,94,.3); border-radius:5px; font-family:'DM Mono',monospace; font-size:.7rem; color:#22c55e; margin-left:auto; }
  .main-layout { position:relative; z-index:1; display:grid; grid-template-columns:1fr 1fr; height:calc(100vh - 73px); }
  .left-panel { border-right:1px solid var(--border); display:flex; flex-direction:column; overflow:hidden; }
  .panel-header { padding:1rem 1.75rem; border-bottom:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; background:var(--surface); flex-shrink:0; }
  .panel-title { font-family:'Syne',sans-serif; font-size:.78rem; font-weight:700; letter-spacing:.08em; text-transform:uppercase; color:var(--muted); }
  .sample-tabs { display:flex; gap:.5rem; padding:.85rem 1.75rem; border-bottom:1px solid var(--border); background:var(--surface); flex-shrink:0; overflow-x:auto; scrollbar-width:none; }
  .sample-tabs::-webkit-scrollbar { display:none; }
  .tab-btn { padding:.35rem .8rem; border-radius:6px; border:1px solid var(--border); background:transparent; color:var(--muted); cursor:pointer; font-size:.76rem; font-family:'DM Mono',monospace; transition:all .15s; white-space:nowrap; }
  .tab-btn:hover { border-color:var(--accent); color:var(--accent); }
  .tab-btn.active { background:var(--accent); border-color:var(--accent); color:#000; font-weight:600; }
  textarea { flex:1; background:var(--bg); color:var(--text); border:none; outline:none; padding:1.5rem 1.75rem; font-family:'DM Mono',monospace; font-size:.8rem; line-height:1.7; resize:none; overflow-y:auto; }
  textarea::placeholder { color:#3a3d45; }
  .action-bar { padding:.85rem 1.75rem; border-top:1px solid var(--border); display:flex; gap:.75rem; align-items:center; background:var(--surface); flex-shrink:0; }
  .process-btn { padding:.6rem 1.6rem; background:linear-gradient(135deg,var(--accent),var(--accent2)); color:#000; border:none; border-radius:8px; font-family:'Syne',sans-serif; font-weight:700; font-size:.88rem; cursor:pointer; transition:all .2s; display:flex; align-items:center; gap:.5rem; }
  .process-btn:hover:not(:disabled) { transform:translateY(-1px); box-shadow:0 4px 20px rgba(240,165,0,.35); }
  .process-btn:disabled { opacity:.5; cursor:not-allowed; }
  .clear-btn { padding:.6rem 1.1rem; background:transparent; color:var(--muted); border:1px solid var(--border); border-radius:8px; font-size:.83rem; cursor:pointer; transition:all .15s; }
  .clear-btn:hover { border-color:var(--muted); color:var(--text); }
  .right-panel { display:flex; flex-direction:column; overflow:hidden; }
  .results-area { flex:1; overflow-y:auto; padding:1.5rem 1.75rem; }
  .results-area::-webkit-scrollbar { width:4px; }
  .results-area::-webkit-scrollbar-thumb { background:var(--border); border-radius:2px; }
  .placeholder { display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; gap:1rem; color:var(--muted); text-align:center; }
  .placeholder .icon { font-size:3rem; opacity:.25; }
  .placeholder p { font-size:.88rem; }
  .loading-state { display:flex; flex-direction:column; align-items:center; justify-content:center; height:100%; gap:1.25rem; }
  .spinner { width:38px; height:38px; border:2px solid var(--border); border-top-color:var(--accent); border-radius:50%; animation:spin .8s linear infinite; }
  @keyframes spin { to { transform:rotate(360deg); } }
  .loading-state p { color:var(--muted); font-size:.85rem; font-family:'DM Mono',monospace; }
  .route-hero { margin-bottom:1.5rem; padding:1.4rem; border-radius:12px; border:1px solid; display:flex; align-items:flex-start; gap:1rem; animation:fadeUp .4s ease; }
  @keyframes fadeUp { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
  .route-icon { font-size:2rem; flex-shrink:0; }
  .route-label { font-family:'Syne',sans-serif; font-size:.68rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; opacity:.7; margin-bottom:.2rem; }
  .route-name { font-family:'Syne',sans-serif; font-size:1.4rem; font-weight:800; letter-spacing:-.02em; margin-bottom:.45rem; }
  .route-reasoning { font-size:.84rem; line-height:1.6; opacity:.85; }
  .route-fast    { background:rgba(34,197,94,.08);  border-color:rgba(34,197,94,.3);  color:#22c55e; }
  .route-manual  { background:rgba(59,130,246,.08); border-color:rgba(59,130,246,.3); color:#3b82f6; }
  .route-invest  { background:rgba(239,68,68,.08);  border-color:rgba(239,68,68,.3);  color:#ef4444; }
  .route-special { background:rgba(168,85,247,.08); border-color:rgba(168,85,247,.3); color:#a855f7; }
  .route-std     { background:rgba(240,165,0,.08);  border-color:rgba(240,165,0,.3);  color:#f0a500; }
  .section { margin-bottom:1.1rem; border:1px solid var(--border); border-radius:10px; overflow:hidden; animation:fadeUp .4s ease; }
  .section-head { padding:.7rem 1.1rem; background:var(--surface2); display:flex; align-items:center; gap:.6rem; }
  .section-title { font-family:'Syne',sans-serif; font-size:.76rem; font-weight:700; letter-spacing:.06em; text-transform:uppercase; }
  .badge { padding:.12rem .45rem; border-radius:4px; font-family:'DM Mono',monospace; font-size:.68rem; }
  .badge-green { background:rgba(34,197,94,.15); color:#22c55e; }
  .badge-red   { background:rgba(239,68,68,.15);  color:#ef4444; }
  .badge-blue  { background:rgba(59,130,246,.15); color:#3b82f6; }
  .section-body { padding:.65rem 1.1rem; }
  .field-row { display:grid; grid-template-columns:155px 1fr; gap:.5rem; padding:.45rem 0; border-bottom:1px solid rgba(37,40,48,.6); font-size:.81rem; }
  .field-row:last-child { border-bottom:none; }
  .field-key { color:var(--muted); font-family:'DM Mono',monospace; font-size:.73rem; padding-top:1px; }
  .field-val { color:var(--text); line-height:1.5; word-break:break-word; }
  .field-val.empty { color:#3a3d45; font-style:italic; }
  .field-val.flagged { color:#ef4444; }
  .missing-list { display:flex; flex-wrap:wrap; gap:.4rem; padding:.7rem 1.1rem; }
  .missing-tag { padding:.25rem .6rem; background:rgba(239,68,68,.1); border:1px solid rgba(239,68,68,.25); border-radius:5px; font-family:'DM Mono',monospace; font-size:.71rem; color:#ef4444; }
  .json-toggle { padding:.45rem .9rem; background:transparent; color:var(--muted); border:1px solid var(--border); border-radius:7px; font-family:'DM Mono',monospace; font-size:.73rem; cursor:pointer; transition:all .15s; }
  .json-toggle:hover { border-color:var(--accent); color:var(--accent); }
  .json-block { background:var(--surface2); border:1px solid var(--border); border-radius:10px; padding:1.1rem; font-family:'DM Mono',monospace; font-size:.74rem; line-height:1.7; overflow-x:auto; white-space:pre; color:#9ca3af; margin-bottom:1rem; animation:fadeUp .3s ease; }
  .json-block .key { color:#60a5fa; }
  .json-block .str { color:#86efac; }
  .json-block .num { color:#fbbf24; }
  .json-block .bool { color:#f472b6; }
  .bottom-bar { padding:.75rem 1.75rem; border-top:1px solid var(--border); display:flex; align-items:center; justify-content:space-between; background:var(--surface); flex-shrink:0; }
  .api-status { display:flex; align-items:center; gap:.4rem; font-size:.73rem; color:var(--muted); font-family:'DM Mono',monospace; }
  .status-dot { width:6px; height:6px; border-radius:50%; background:var(--green); box-shadow:0 0 6px var(--green); animation:pulse 2s infinite; }
  @keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }
  .error-box { padding:1.1rem; background:rgba(239,68,68,.08); border:1px solid rgba(239,68,68,.3); border-radius:10px; color:#ef4444; font-size:.84rem; margin-bottom:1rem; }
</style>
</head>
<body>
<header>
  <div class="logo-mark">FN</div>
  <div>
    <h1>FNOL <span>Agent</span></h1>
    <p>First Notice of Loss — Regex-Powered Claims Processor</p>
  </div>

</header>

<div class="main-layout">
  <!-- LEFT -->
  <div class="left-panel">
    <div class="panel-header">
      <span class="panel-title"> FNOL Document</span>
      <span style="font-size:.73rem;color:var(--muted);font-family:'DM Mono',monospace;">paste plain text</span>
    </div>
    <div class="sample-tabs">
      <button class="tab-btn" onclick="loadSample('fnol_001')">001 · Auto</button>
      <button class="tab-btn" onclick="loadSample('fnol_002')">002 · Property</button>
      <button class="tab-btn" onclick="loadSample('fnol_003')">003 · Injury</button>
      <button class="tab-btn" onclick="loadSample('fnol_004')">004 · Fraud</button>
      <button class="tab-btn" onclick="loadSample('fnol_005')">005 · Missing</button>
    </div>
    <textarea id="fnolInput" placeholder="Paste an FNOL document here, or click a sample above..."></textarea>
    <div class="action-bar">
      <button class="process-btn" id="processBtn" onclick="processFNOL()">⚡ Process Claim</button>
      <button class="clear-btn" onclick="clearAll()">Clear</button>
      <span id="charCount" style="font-size:.73rem;color:var(--muted);font-family:'DM Mono',monospace;margin-left:auto;"></span>
    </div>
  </div>

  <!-- RIGHT -->
  <div class="right-panel">
    <div class="panel-header">
      <span class="panel-title"> Agent Output</span>
      <button class="json-toggle" id="jsonToggle" onclick="toggleJson()" style="display:none;">{ } View JSON</button>
    </div>
    <div class="results-area" id="resultsArea">
      <div class="placeholder">
        <div class="icon">⚡</div>
        <p>Load a sample or paste an FNOL document,<br>then click <strong>Process Claim</strong></p>
        <p style="font-size:.78rem;margin-top:.25rem;">Runs entirely via regex — instant, no internet needed</p>
      </div>
    </div>
    <div class="bottom-bar">
      <div class="api-status"><div class="status-dot"></div>Regex engine · zero dependencies</div>
      <span id="processTime" style="font-size:.73rem;color:var(--muted);font-family:'DM Mono',monospace;"></span>
    </div>
  </div>
</div>

<script>
const SAMPLES = {{ samples | tojson }};
let currentResult = null, showJson = false;

document.getElementById('fnolInput').addEventListener('input', function() {
  const n = this.value.length;
  document.getElementById('charCount').textContent = n ? n + ' chars' : '';
});

function loadSample(key) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  event.target.classList.add('active');
  document.getElementById('fnolInput').value = SAMPLES[key] || '';
  document.getElementById('fnolInput').dispatchEvent(new Event('input'));
  clearResults();
}

function clearAll() {
  document.getElementById('fnolInput').value = '';
  document.getElementById('charCount').textContent = '';
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  clearResults();
}

function clearResults() {
  currentResult = null; showJson = false;
  document.getElementById('jsonToggle').style.display = 'none';
  document.getElementById('processTime').textContent = '';
  document.getElementById('resultsArea').innerHTML = `<div class="placeholder"><div class="icon">⚡</div><p>Load a sample or paste an FNOL document,<br>then click <strong>Process Claim</strong></p><p style="font-size:.78rem;margin-top:.25rem;">Runs entirely via regex — instant, no internet needed</p></div>`;
}

function routeClass(r) {
  const s = r.toLowerCase();
  if (s.includes('fast')) return 'route-fast';
  if (s.includes('manual')) return 'route-manual';
  if (s.includes('invest')) return 'route-invest';
  if (s.includes('special')) return 'route-special';
  return 'route-std';
}
function routeIcon(r) {
  const s = r.toLowerCase();
  if (s.includes('fast')) return '';
  if (s.includes('manual')) return '';
  if (s.includes('invest')) return '';
  if (s.includes('special')) return '';
  return '';
}
function fmtKey(k) { return k.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase()); }

function syntaxHighlight(obj) {
  return JSON.stringify(obj,null,2).replace(/("(?:\\u[a-zA-Z0-9]{4}|\\[^u]|[^\\"])*"(\s*:)?|\b(?:true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g, m => {
    let c = 'num';
    if (/^"/.test(m)) c = /:$/.test(m) ? 'key' : 'str';
    else if (/true|false/.test(m)) c = 'bool';
    return `<span class="${c}">${m}</span>`;
  });
}

function renderResults(data) {
  currentResult = data;
  const f = data.extractedFields, missing = data.missingFields, route = data.recommendedRoute;
  const missingSet = new Set(missing);

  const groups = {
    'Policy Information': ['policy_number','policyholder_name','effective_date_start','effective_date_end'],
    'Incident Details':   ['incident_date','incident_time','incident_location','incident_description'],
    'Involved Parties':   ['claimant_name','third_parties','claimant_contact','third_party_contact'],
    'Asset Details':      ['asset_type','asset_id','estimated_damage'],
    'Claim Details':      ['claim_type','attachments','initial_estimate'],
  };

  let html = `<div class="route-hero ${routeClass(route)}">
    <div class="route-icon">${routeIcon(route)}</div>
    <div>
      <div class="route-label">Recommended Route</div>
      <div class="route-name">${route}</div>
      <div class="route-reasoning">${data.reasoning}</div>
    </div>
  </div>`;

  if (missing.length) {
    html += `<div class="section"><div class="section-head"><span class="section-title">⚠ Missing Fields</span><span class="badge badge-red">${missing.length} missing</span></div><div class="missing-list">`;
    missing.forEach(m => { html += `<span class="missing-tag">${fmtKey(m)}</span>`; });
    html += `</div></div>`;
  }

  for (const [grp, keys] of Object.entries(groups)) {
    const filled = keys.filter(k => f[k] && f[k].trim()).length;
    html += `<div class="section"><div class="section-head"><span class="section-title">${grp}</span><span class="badge badge-blue">${filled}/${keys.length}</span></div><div class="section-body">`;
    keys.forEach(k => {
      const val = f[k] || '';
      const empty = !val.trim();
      const flagged = missingSet.has(k);
      html += `<div class="field-row"><div class="field-key">${fmtKey(k)}</div><div class="field-val ${empty?'empty':''} ${flagged?'flagged':''}">${empty?'— not found':val}</div></div>`;
    });
    html += `</div></div>`;
  }

  document.getElementById('resultsArea').innerHTML = html;
  document.getElementById('jsonToggle').style.display = 'inline-block';
}

function toggleJson() {
  if (!currentResult) return;
  showJson = !showJson;
  const area = document.getElementById('resultsArea');
  const btn  = document.getElementById('jsonToggle');
  if (showJson) {
    btn.textContent = '✕ Hide JSON';
    const b = document.createElement('div');
    b.className = 'json-block';
    b.innerHTML = syntaxHighlight(currentResult);
    area.insertBefore(b, area.firstChild);
  } else {
    btn.textContent = '{ } View JSON';
    const ex = area.querySelector('.json-block');
    if (ex) ex.remove();
  }
}

async function processFNOL() {
  const text = document.getElementById('fnolInput').value.trim();
  if (!text) { alert('Paste an FNOL document or load a sample first.'); return; }
  const btn = document.getElementById('processBtn');
  btn.disabled = true;
  const t0 = Date.now();
  document.getElementById('jsonToggle').style.display = 'none';
  document.getElementById('processTime').textContent = '';
  document.getElementById('resultsArea').innerHTML = `<div class="loading-state"><div class="spinner"></div><p>Extracting fields via regex patterns...</p></div>`;

  try {
    const resp = await fetch('/process', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({ text })
    });
    const data = await resp.json();
    const elapsed = ((Date.now()-t0)/1000).toFixed(2);
    document.getElementById('processTime').textContent = `⏱ ${elapsed}s`;
    if (data.error) {
      document.getElementById('resultsArea').innerHTML = `<div class="error-box"> <strong>Error:</strong> ${data.error}</div>`;
    } else {
      renderResults(data);
    }
  } catch(e) {
    document.getElementById('resultsArea').innerHTML = `<div class="error-box"> Network error: ${e.message}</div>`;
  } finally {
    btn.disabled = false;
  }
}
</script>
</body>
</html>
"""

def load_samples():
    sample_dir = Path(__file__).parent / "sample_fnols"
    return {f.stem: f.read_text(encoding="utf-8") for f in sorted(sample_dir.glob("*.txt"))}

@app.route("/")
def index():
    return render_template_string(HTML_TEMPLATE, samples=load_samples())

@app.route("/process", methods=["POST"])
def process():
    data = request.get_json()
    text = (data or {}).get("text", "").strip()
    if not text:
        return jsonify({"error": "No FNOL text provided"}), 400
    try:
        result = process_fnol(text, source_file="web-upload")
        result.pop("source_file", None)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("\n FNOL Agent Web UI  (regex mode)")
    print("   Visit: http://localhost:5000\n")
    app.run(debug=True, port=5000)