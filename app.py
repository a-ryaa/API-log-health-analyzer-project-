"""
app.py  -  API Health Log Analyzer (website)
--------------------------------------------
A small Flask website. The visitor uploads an API log file and the site
shows the health dashboard for that file. It reuses the functions of
log_analyzer.py, so no analysis code is repeated.

Run:    pip install flask
        python app.py
Open:   http://127.0.0.1:5000

Routes:
    GET  /              upload page
    POST /analyze       analyze the uploaded file and show the dashboard
    GET  /sample        analyze the sample log (api_health.log)
    POST /api/analyze   send log text in the body, get the report as JSON
"""

from html import escape
from pathlib import Path

from flask import Flask, jsonify, request

import dashboard
import generate_logs
import log_analyzer as la

SAMPLE = Path(__file__).parent / "api_health.log"

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024      # upload limit: 5 MB

EXTRA_CSS = """
.hero{background:linear-gradient(120deg,#0B1B2B 0%,#12304A 55%,#0E7C89 100%);color:#fff;text-align:center;
padding:46px 20px 110px}.hero h1{margin:0 0 10px;font-size:38px;line-height:1.15}
.hero p{margin:0 auto;max-width:560px;color:#BCD8EA;font-size:17px}
.feats{margin-top:20px;display:flex;flex-wrap:wrap;gap:10px;justify-content:center}
.upcard{max-width:640px;margin:-80px auto 0;padding:26px;position:relative}
.dz{display:block;border:2px dashed #8FB8DE;border-radius:14px;padding:30px 20px;text-align:center;
background:#F5FAFD;cursor:pointer;transition:.15s}.dz:hover,.dz.over{background:#E4F4F6;border-color:#0E9AA7}
.dz svg{width:46px;height:46px;color:#0E9AA7}.dz .t{font-size:17px;font-weight:700;margin-top:8px}
.dz .s{color:#5B7C99;font-size:13.5px;margin-top:4px}.dz .f{margin-top:10px;font-weight:700;color:#0E7C89}
.actions{display:flex;flex-wrap:wrap;gap:12px;justify-content:center;align-items:center;margin-top:18px}
button.go{background:linear-gradient(135deg,#19C2CF,#0E9AA7);color:#fff;border:0;border-radius:10px;
padding:12px 28px;font-size:15px;font-weight:700;cursor:pointer;box-shadow:0 6px 16px rgba(14,154,167,.35)}
button.go:hover{transform:translateY(-1px)}
a.alt{color:#0E7C89;border:2px solid #0E9AA7;border-radius:10px;padding:10px 22px;font-weight:700;
text-decoration:none;font-size:15px}a.alt:hover{background:#E4F4F6}
.error{background:#FBE3E3;color:#B02A2A;border-radius:10px;padding:11px 14px;margin-bottom:16px;font-weight:600}
.steps{max-width:900px;margin:34px auto 0;display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}
.step{padding:18px 20px}.num{width:34px;height:34px;border-radius:50%;background:#0E9AA7;color:#fff;
display:grid;place-items:center;font-weight:700;margin-bottom:10px}.step h2{margin:0 0 6px;font-size:16px}
.step p{margin:0;color:#5B7C99;font-size:14px}
.fmt{max-width:900px;margin:16px auto 0}
code{background:#EAF2F7;padding:3px 8px;border-radius:6px;font-size:13px}
"""

UPLOAD_JS = """
const dz = document.getElementById('dz'), file = document.getElementById('f');
const show = () => { document.getElementById('fname').textContent = file.files.length ? file.files[0].name : ''; };
file.addEventListener('change', show);
['dragenter', 'dragover'].forEach(e => dz.addEventListener(e, ev => { ev.preventDefault(); dz.classList.add('over'); }));
['dragleave', 'drop'].forEach(e => dz.addEventListener(e, ev => { ev.preventDefault(); dz.classList.remove('over'); }));
dz.addEventListener('drop', ev => { file.files = ev.dataTransfer.files; show(); });
document.getElementById('form').addEventListener('submit', () => {
  document.getElementById('go').textContent = 'Analyzing...';
});
"""


def page(body, title="API Health Log Analyzer", script=""):
    """Wrap some HTML in a complete page that uses the dashboard styles."""
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width, initial-scale=1">'
            f"<title>{title}</title><style>{dashboard.CSS}{EXTRA_CSS}</style></head>"
            f"<body>{body}<script>{script}</script></body></html>")


def upload_page(error=""):
    error_box = f'<div class="error">{escape(error)}</div>' if error else ""
    chips = "".join(f'<span class="chip">{c}</span>' for c in
                    ("Success and error rates", "Response times", "Charts and alerts", "JSON API"))
    steps = "".join(
        f'<div class="card step"><div class="num">{n}</div><h2>{t}</h2><p>{d}</p></div>'
        for n, t, d in (("1", "Upload", "Choose your API log file, or try the built-in sample."),
                        ("2", "Analyze", "Python parses every line and calculates the health of each endpoint."),
                        ("3", "See the dashboard", "Status banner, charts, alerts and a table appear instantly.")))
    return page(
        dashboard.page_header("API Health Log Analyzer", ["MCA (CC&amp;D) Python mini project"])
        + '<div class="hero"><h1>Check the health of your API<br>in seconds</h1>'
        "<p>Upload an API log file and get a clear dashboard with charts, alerts and response times.</p>"
        f'<div class="feats">{chips}</div></div>'
        f'<div class="card upcard">{error_box}'
        '<form id="form" action="/analyze" method="post" enctype="multipart/form-data">'
        f'<label class="dz" id="dz"><input type="file" name="logfile" id="f" accept=".log,.txt" hidden>'
        f'{dashboard.icon("upload")}<div class="t">Drag and drop your log file here</div>'
        '<div class="s">or click to browse (.log or .txt, up to 5 MB)</div><div class="f" id="fname"></div></label>'
        '<div class="actions"><button class="go" id="go" type="submit">Analyze log</button>'
        '<a class="alt" href="/sample">Try the sample log</a></div></form></div>'
        f'<div class="steps">{steps}</div>'
        '<div class="card fmt"><h2>Expected log format</h2>'
        "<code>2026-10-03 08:00:12 | GET | /api/users | 200 | 120</code>"
        '<p style="color:#5B7C99;font-size:14px;margin-bottom:0">Fields: date, time, method, endpoint, '
        "status code, response time in ms.</p></div>"
        '<div class="foot">API Health Log Analyzer &nbsp;|&nbsp; MCA (CC&amp;D) Python mini project</div>',
        script=UPLOAD_JS,
    )


def show_dashboard(text, name):
    """Parse the log text and return the dashboard page (or the upload page with an error)."""
    entries, bad_lines = la.parse_lines(text.splitlines())
    if not entries:
        return upload_page("No valid log lines found. Check the file against the format below."), 400
    results = la.analyze(entries)
    summary = la.overall_summary(entries)
    return dashboard.build_dashboard(summary, results, name, bad_lines)


@app.route("/")
def home():
    return upload_page()


@app.route("/analyze", methods=["POST"])
def analyze_upload():
    file = request.files.get("logfile")
    if file is None or file.filename == "":
        return upload_page("Please choose a log file first."), 400
    text = file.read().decode("utf-8", errors="replace")
    return show_dashboard(text, file.filename)


@app.route("/sample")
def sample():
    if not SAMPLE.exists():                     # create the sample log if it is missing
        generate_logs.generate(str(SAMPLE))
    return show_dashboard(SAMPLE.read_text(), "api_health.log (sample)")


@app.route("/api/analyze", methods=["POST"])
def api_analyze():
    entries, bad_lines = la.parse_lines(request.get_data(as_text=True).splitlines())
    if not entries:
        return jsonify(error="no valid log lines found"), 400
    return jsonify(summary=la.overall_summary(entries), endpoints=la.analyze(entries),
                   skipped_lines=bad_lines)


@app.errorhandler(413)
def too_large(_error):
    return upload_page("The file is too large. The limit is 5 MB."), 413


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
