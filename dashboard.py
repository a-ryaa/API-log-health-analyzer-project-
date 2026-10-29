"""
dashboard.py  -  builds the dashboard page shown by the website
----------------------------------------------------------------
Every chart is drawn as inline SVG by plain Python, so the page needs no
chart library and no internet connection. app.py calls build_dashboard().
"""

from html import escape

COLORS = {"HEALTHY": "#2E9E6B", "DEGRADED": "#F2A541", "CRITICAL": "#D64545"}
TINTS = {"HEALTHY": "#DDF3E8", "DEGRADED": "#FDF0D9", "CRITICAL": "#FBE3E3"}
INKS = {"HEALTHY": "#1F7A4D", "DEGRADED": "#8A5200", "CRITICAL": "#B02A2A"}

ICONS = {
    "activity": '<polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>',
    "check": '<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/>',
    "alert": ('<path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>'
              '<line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/>'),
    "clock": '<circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/>',
    "zap": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "upload": ('<polyline points="16 16 12 12 8 16"/><line x1="12" y1="12" x2="12" y2="21"/>'
               '<path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"/>'),
}
TONES = {"teal": ("#E0F5F7", "#0E9AA7"), "green": ("#DDF3E8", "#1F7A4D"), "red": ("#FBE3E3", "#B02A2A"),
         "amber": ("#FDF0D9", "#B26B00"), "indigo": ("#E6E9FB", "#4650C8")}

CSS = """
:root{--ink:#0B1B2B;--navy:#12304A;--teal:#0E9AA7;--mute:#5B7C99;--line:#E3EAF0}
*{box-sizing:border-box}
body{margin:0;font-family:"Segoe UI",system-ui,Arial,sans-serif;color:var(--ink);min-height:100vh;
background:radial-gradient(circle at 10% -10%,#D7F0F2 0,transparent 38%),
radial-gradient(circle at 95% 0,#E3E9FA 0,transparent 35%),#F2F6FA}
svg.i{fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}
.top{background:linear-gradient(120deg,#0B1B2B 0%,#12304A 55%,#0E7C89 100%);color:#fff;padding:20px 32px;
display:flex;flex-wrap:wrap;gap:14px;justify-content:space-between;align-items:center}
.brand{display:flex;align-items:center;gap:14px}
.logo{width:48px;height:48px;border-radius:14px;background:linear-gradient(135deg,#19C2CF,#0E9AA7);color:#fff;
display:grid;place-items:center;box-shadow:0 4px 16px rgba(14,154,167,.5)}.logo svg{width:26px;height:26px}
.top h1{margin:0;font-size:22px;letter-spacing:.2px}
.meta{margin-top:6px;display:flex;flex-wrap:wrap;gap:8px}
.chip{background:rgba(255,255,255,.13);border-radius:20px;padding:3px 12px;font-size:12.5px;color:#D3E8F6}
.btn{background:#fff;color:#0E7C89;border:0;border-radius:10px;padding:10px 20px;font-size:14px;
font-weight:700;text-decoration:none;cursor:pointer;display:inline-block;transition:.15s}
.btn:hover{transform:translateY(-1px);box-shadow:0 6px 16px rgba(0,0,0,.22)}
.wrap{max-width:1200px;margin:0 auto;padding:24px 20px 6px}
.banner{border-radius:16px;padding:18px 22px;margin-bottom:18px;display:flex;align-items:center;gap:16px;
border:1px solid rgba(0,0,0,.05)}.banner b{font-size:19px}.banner .sub{font-size:14px;opacity:.85}
.pulse{width:16px;height:16px;border-radius:50%;flex:none;box-shadow:0 0 0 6px rgba(255,255,255,.7)}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:16px;margin-bottom:18px}
.kpi,.card{background:#fff;border-radius:16px;border:1px solid #EDF2F7;transition:.15s;
box-shadow:0 2px 6px rgba(18,48,74,.06),0 8px 24px rgba(18,48,74,.07)}
.kpi:hover,.card:hover{transform:translateY(-2px)}
.kpi{padding:16px 18px;display:flex;align-items:center;gap:14px}
.ico{width:46px;height:46px;border-radius:14px;display:grid;place-items:center;flex:none}.ico svg{width:23px;height:23px}
.kpi b{display:block;font-size:26px;line-height:1.1}.kpi span{color:var(--mute);font-size:13px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(340px,1fr));gap:18px;margin-bottom:18px}
.card{padding:18px 20px}.card h2{font-size:15.5px;margin:0 0 14px;color:var(--navy)}
.chart{width:100%;height:auto;display:block}.chart .lbl{font-size:11px;fill:#0B1B2B}
.chart .val,.chart .axis{font-size:10px;fill:#5B7C99}.chart .grid{stroke:#E3EAF0;stroke-width:1}
.chart .limit{stroke:#8FB8DE;stroke-width:1;stroke-dasharray:3 3}
.donutbox{display:flex;align-items:center;gap:18px;flex-wrap:wrap}.donut{width:150px;flex:none}
.donut .big{font-size:6px;font-weight:700;fill:#0B1B2B}.donut .small{font-size:2.6px;fill:#5B7C99}
.legend{list-style:none;margin:0;padding:0;font-size:14px}.legend li{margin:6px 0}
.legend i,.key i{display:inline-block;width:11px;height:11px;border-radius:3px;margin-right:7px}
.key{font-size:13px;color:#5B7C99;margin-bottom:6px}.key i{margin-left:10px}.key i:first-child{margin-left:0}
.alert{margin:10px 0;font-size:14px}.detail{color:#5B7C99;font-size:12px;margin-top:3px}
.empty{color:#5B7C99;font-size:14px}
.scroll{overflow-x:auto}
table{width:100%;border-collapse:collapse;font-size:14px}
th,td{padding:10px 8px;text-align:right;border-bottom:1px solid var(--line)}
th:first-child,td:first-child{text-align:left}
th{color:#5B7C99;font-weight:600;font-size:12.5px;text-transform:uppercase;letter-spacing:.4px}
tbody tr:nth-child(even){background:#F8FBFD}tbody tr:hover{background:#EAF6F8}
.badge{padding:3px 11px;border-radius:12px;font-weight:700;font-size:12px}
.foot{text-align:center;color:#5B7C99;font-size:12.5px;padding:14px 0 26px}
"""


def icon(name):
    return f'<svg class="i" viewBox="0 0 24 24">{ICONS[name]}</svg>'


def nice_top(value):
    """Round a chart maximum up, so the 3 grid steps are round numbers (0, 2000, 4000, 6000)."""
    step = 1
    while True:
        for factor in (1, 2, 5):
            if step * factor * 3 >= value:
                return step * factor * 3
        step *= 10


def donut(parts, big, small):
    """Donut chart. parts is a list of (label, value, color)."""
    total = sum(v for _, v, _ in parts) or 1
    rings, offset = "", 25                       # 25 makes the first slice start at the top
    for label, v, color in parts:
        pct = v / total * 100
        if pct:
            rings += (f'<circle cx="21" cy="21" r="15.9155" fill="none" stroke="{color}" stroke-width="5" '
                      f'stroke-dasharray="{pct:.2f} {100 - pct:.2f}" stroke-dashoffset="{offset:.2f}">'
                      f"<title>{escape(label)}: {v}</title></circle>")
        offset -= pct
    legend = "".join(f'<li><i style="background:{c}"></i>{escape(l)} <b>{v}</b></li>' for l, v, c in parts)
    return ('<div class="donutbox"><svg viewBox="0 0 42 42" class="donut">'
            '<circle cx="21" cy="21" r="15.9155" fill="none" stroke="#EAF2F7" stroke-width="5"/>'
            f'{rings}<text x="21" y="21.8" text-anchor="middle" class="big">{big}</text>'
            f'<text x="21" y="26.5" text-anchor="middle" class="small">{small}</text></svg>'
            f'<ul class="legend">{legend}</ul></div>')


def error_bars(results):
    """Horizontal bars: error rate per endpoint, with the 5% and 15% limits marked."""
    top = max(15, max(r["error_rate"] for r in results)) * 1.1
    rows, row_h = "", 30
    for i, r in enumerate(results):
        y = 8 + i * row_h
        width = r["error_rate"] / top * 215
        rows += (f'<text x="0" y="{y + 12}" class="lbl">{escape(r["endpoint"])}</text>'
                 f'<rect x="100" y="{y}" width="215" height="16" rx="4" fill="#EAF2F7"/>'
                 f'<rect x="100" y="{y}" width="{width:.1f}" height="16" rx="4" fill="{COLORS[r["status"]]}">'
                 f'<title>{escape(r["endpoint"])}: {r["error_rate"]}% errors</title></rect>'
                 f'<text x="320" y="{y + 12}" class="val">{r["error_rate"]}%</text>')
    height = 8 + len(results) * row_h
    limits = ""
    for limit in (5, 15):
        x = 100 + limit / top * 215
        limits += (f'<line x1="{x:.1f}" y1="0" x2="{x:.1f}" y2="{height}" class="limit"/>'
                   f'<text x="{x:.1f}" y="{height + 11}" text-anchor="middle" class="axis">{limit}%</text>')
    return f'<svg viewBox="0 0 360 {height + 16}" class="chart">{limits}{rows}</svg>'


def time_columns(results):
    """Grouped columns: average and P95 response time per endpoint."""
    top = nice_top(max(r["p95_ms"] for r in results) * 1.05)
    x0, base, chart_h = 40, 150, 130
    grid = ""
    for k in range(4):
        value = top * k / 3
        y = base - value / top * chart_h
        grid += (f'<line x1="{x0}" y1="{y:.1f}" x2="352" y2="{y:.1f}" class="grid"/>'
                 f'<text x="{x0 - 5}" y="{y + 3:.1f}" text-anchor="end" class="axis">{value:.0f}</text>')
    slot = (352 - x0) / len(results)
    bars = ""
    for i, r in enumerate(results):
        cx = x0 + slot * (i + 0.5)
        for dx, key, color in ((-9, "avg_ms", "#0E9AA7"), (1, "p95_ms", "#12304A")):
            h = r[key] / top * chart_h
            bars += (f'<rect x="{cx + dx:.1f}" y="{base - h:.1f}" width="8" height="{h:.1f}" rx="1.5" '
                     f'fill="{color}"><title>{escape(r["endpoint"])} {key}: {r[key]} ms</title></rect>')
        bars += (f'<text x="{cx:.1f}" y="{base + 13}" text-anchor="middle" class="axis">'
                 f'{escape(r["endpoint"].split("/")[-1][:8])}</text>')
    key = ('<div class="key"><i style="background:#0E9AA7"></i>Average'
           '<i style="background:#12304A"></i>P95 (ms)</div>')
    return f'{key}<svg viewBox="0 0 360 165" class="chart">{grid}{bars}</svg>'


def hour_line(hours):
    """Line chart: number of errors in each hour of the log."""
    if not hours:
        return '<div class="empty">No errors recorded.</div>'
    items = list(hours.items())
    top = nice_top(max(n for _, n in items) * 1.1)
    x0, x1, base, chart_h = 32, 345, 135, 110
    points = []
    for i, (hour, n) in enumerate(items):
        x = x0 + (x1 - x0) * (i / (len(items) - 1) if len(items) > 1 else 0.5)
        points.append((x, base - n / top * chart_h, hour, n))
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y, _, _ in points)
    area = f"{points[0][0]:.1f},{base} {line} {points[-1][0]:.1f},{base}"
    grid = ""
    for k in range(4):
        value = top * k / 3
        y = base - value / top * chart_h
        grid += (f'<line x1="{x0}" y1="{y:.1f}" x2="{x1 + 5}" y2="{y:.1f}" class="grid"/>'
                 f'<text x="{x0 - 5}" y="{y + 3:.1f}" text-anchor="end" class="axis">{value:.0f}</text>')
    dots = "".join(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="4" fill="#0E9AA7"><title>{h}:00 - {n} errors</title>'
                   f'</circle><text x="{x:.1f}" y="{base + 14}" text-anchor="middle" class="axis">{h}:00</text>'
                   for x, y, h, n in points)
    return (f'<svg viewBox="0 0 360 155" class="chart">{grid}<polygon points="{area}" fill="#0E9AA7" '
            f'opacity=".15"/><polyline points="{line}" fill="none" stroke="#0E9AA7" stroke-width="2.5"/>{dots}</svg>')


def kpi(name, tone, value, label):
    bg, fg = TONES[tone]
    return (f'<div class="kpi"><div class="ico" style="background:{bg};color:{fg}">{icon(name)}</div>'
            f"<div><b>{value}</b><span>{label}</span></div></div>")


def badge(status):
    return f'<span class="badge" style="background:{TINTS[status]};color:{INKS[status]}">{status}</span>'


def page_header(title, chips, button=""):
    """The dark gradient bar at the top of every page."""
    chip_html = "".join(f'<span class="chip">{c}</span>' for c in chips)
    return (f'<div class="top"><div class="brand"><div class="logo">{icon("activity")}</div><div>'
            f'<h1>{title}</h1><div class="meta">{chip_html}</div></div></div>{button}</div>')


def build_dashboard(summary, results, name="", bad_lines=0):
    """Return the complete dashboard page as one HTML string."""
    counts = {s: sum(1 for r in results if r["status"] == s) for s in COLORS}
    worst = "CRITICAL" if counts["CRITICAL"] else "DEGRADED" if counts["DEGRADED"] else "HEALTHY"
    banner = (f'<div class="banner" style="background:linear-gradient(90deg,{TINTS[worst]},#fff);'
              f'color:{INKS[worst]}"><span class="pulse" style="background:{COLORS[worst]}"></span><div>'
              f'<b>Overall status: {worst}</b><br><span class="sub">{counts["CRITICAL"]} critical, '
              f'{counts["DEGRADED"]} degraded and {counts["HEALTHY"]} healthy endpoints</span></div></div>')

    codes = summary["status_codes"]
    ok = sum(n for c, n in codes.items() if c < 400)
    client = sum(n for c, n in codes.items() if 400 <= c < 500)
    server = sum(n for c, n in codes.items() if c >= 500)
    health_donut = donut([(s.title(), counts[s], COLORS[s]) for s in COLORS], len(results), "endpoints")
    result_donut = donut([("Success (2xx, 3xx)", ok, "#2E9E6B"), ("Client errors (4xx)", client, "#F2A541"),
                          ("Server errors (5xx)", server, "#D64545")],
                         f'{summary["overall_success_rate"]}%', "success")

    alerts = "".join(
        f'<div class="alert">{badge(r["status"])} &nbsp;<b>{escape(r["endpoint"])}</b>'
        f'<div class="detail">{r["error_rate"]}% errors, average {r["avg_ms"]} ms</div></div>'
        for r in results if r["status"] != "HEALTHY"
    ) or '<div class="empty">All endpoints are healthy.</div>'

    rows = "".join(
        f'<tr><td>{escape(r["endpoint"])}</td><td>{r["requests"]}</td><td>{r["error_rate"]}%</td>'
        f'<td>{r["4xx"]}</td><td>{r["5xx"]}</td><td>{r["avg_ms"]}</td><td>{r["p95_ms"]}</td>'
        f'<td>{badge(r["status"])}</td></tr>' for r in results)

    kpis = "".join([
        kpi("activity", "teal", summary["total_requests"], "Total requests"),
        kpi("check", "green", f'{summary["overall_success_rate"]}%', "Success rate"),
        kpi("alert", "red", f'{summary["overall_error_rate"]}%', f'Error rate ({summary["total_errors"]} errors)'),
        kpi("clock", "amber", f'{summary["avg_response_ms"]} ms', "Average response"),
        kpi("zap", "indigo", f'{summary["p95_response_ms"]} ms', "95th percentile response"),
    ])
    header = page_header("API Health Dashboard",
                         [escape(name), f'{summary["total_requests"]} requests', f"{bad_lines} skipped lines"],
                         '<a class="btn" href="/">Analyze another file</a>')

    return (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>API Health Dashboard</title><style>{CSS}</style></head><body>{header}"
        f'<div class="wrap">{banner}<div class="kpis">{kpis}</div>'
        '<div class="grid">'
        f'<div class="card"><h2>Endpoint health</h2>{health_donut}</div>'
        f'<div class="card"><h2>Requests by result</h2>{result_donut}</div>'
        f'<div class="card"><h2>Alerts</h2>{alerts}</div></div>'
        '<div class="grid">'
        f'<div class="card"><h2>Error rate by endpoint</h2>{error_bars(results)}</div>'
        f'<div class="card"><h2>Response time by endpoint (ms)</h2>{time_columns(results)}</div>'
        f'<div class="card"><h2>Errors by hour</h2>{hour_line(summary["errors_by_hour"])}</div></div>'
        '<div class="card tablecard"><h2>Endpoint health table</h2><div class="scroll"><table><thead><tr><th>Endpoint</th>'
        '<th>Requests</th><th>Error %</th><th>4xx</th><th>5xx</th><th>Avg ms</th><th>P95 ms</th>'
        f"<th>Status</th></tr></thead><tbody>{rows}</tbody></table></div></div></div>"
        '<div class="foot">API Health Log Analyzer &nbsp;|&nbsp; MCA (CC&amp;D) Python mini project</div>'
        "</body></html>"
    )
