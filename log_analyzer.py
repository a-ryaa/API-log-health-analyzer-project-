"""
log_analyzer.py  -  API Health Log Analyzer
-------------------------------------------
Reads an API log file, calculates health metrics (success rate, error rate,
response times) for every endpoint, assigns a health status, and saves
the report as text, CSV and JSON.

Usage:
    python log_analyzer.py                       # analyzes api_health.log
    python log_analyzer.py --file mylog.log
    python log_analyzer.py --slow 800 --top 3
"""

import argparse
import csv
import json
import re
import statistics
from collections import Counter, defaultdict

# ---------- Configuration ----------
LOG_PATTERN = re.compile(
    r"^(?P<date>\d{4}-\d{2}-\d{2}) (?P<time>\d{2}:\d{2}:\d{2}) \| "
    r"(?P<method>[A-Z]+) \| (?P<endpoint>\S+) \| "
    r"(?P<status>\d{3}) \| (?P<rt>\d+)$"
)


# ---------- Step 1: Parse ----------
def parse_lines(lines):
    """Parse an iterable of log lines. Returns (valid entries, number of bad lines)."""
    entries, bad_lines = [], 0
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = LOG_PATTERN.match(line)
        if match:
            entries.append({
                "hour": match["time"][:2],
                "method": match["method"],
                "endpoint": match["endpoint"],
                "status": int(match["status"]),
                "rt": int(match["rt"]),
            })
        else:
            bad_lines += 1
    return entries, bad_lines


def parse_log(filename):
    """Read the file and return (list of valid entries, number of bad lines)."""
    try:
        with open(filename) as f:
            return parse_lines(f)
    except FileNotFoundError:
        print(f"Error: file '{filename}' not found. Run generate_logs.py first.")
        raise SystemExit(1)


# ---------- Step 2: Calculate metrics ----------
def percentile(values, p):
    """Simple percentile (e.g. p=95) without external libraries."""
    ordered = sorted(values)
    index = max(0, int(round(p / 100 * len(ordered))) - 1)
    return ordered[index]


def health_status(error_rate, avg_rt):
    """Rule-based health classification."""
    if error_rate > 15 or avg_rt > 1500:
        return "CRITICAL"
    if error_rate > 5 or avg_rt > 600:
        return "DEGRADED"
    return "HEALTHY"


def analyze(entries):
    by_endpoint = defaultdict(list)
    for e in entries:
        by_endpoint[e["endpoint"]].append(e)

    results = []
    for endpoint, rows in by_endpoint.items():
        total = len(rows)
        times = [r["rt"] for r in rows]
        client_err = sum(1 for r in rows if 400 <= r["status"] < 500)
        server_err = sum(1 for r in rows if r["status"] >= 500)
        error_rate = (client_err + server_err) / total * 100
        avg_rt = statistics.mean(times)
        results.append({
            "endpoint": endpoint,
            "requests": total,
            "success_rate": round(100 - error_rate, 2),
            "error_rate": round(error_rate, 2),
            "4xx": client_err,
            "5xx": server_err,
            "avg_ms": round(avg_rt, 1),
            "min_ms": min(times),
            "max_ms": max(times),
            "p95_ms": percentile(times, 95),
            "status": health_status(error_rate, avg_rt),
        })
    return sorted(results, key=lambda r: r["error_rate"], reverse=True)


def overall_summary(entries):
    total = len(entries)
    errors = sum(1 for e in entries if e["status"] >= 400)
    times = [e["rt"] for e in entries]
    return {
        "total_requests": total,
        "total_errors": errors,
        "overall_error_rate": round(errors / total * 100, 2),
        "overall_success_rate": round(100 - errors / total * 100, 2),
        "avg_response_ms": round(statistics.mean(times), 1),
        "median_response_ms": statistics.median(times),
        "p95_response_ms": percentile(times, 95),
        "status_codes": dict(sorted(Counter(e["status"] for e in entries).items())),
        "errors_by_hour": dict(sorted(Counter(
            e["hour"] for e in entries if e["status"] >= 400).items())),
    }


# ---------- Step 3: Report ----------
def print_report(summary, results, bad_lines, slow_limit, top_n, entries):
    line = "=" * 78
    print(line)
    print("                     API HEALTH LOG ANALYSIS REPORT")
    print(line)
    print(f"Total requests     : {summary['total_requests']}")
    print(f"Success rate       : {summary['overall_success_rate']}%")
    print(f"Error rate         : {summary['overall_error_rate']}%")
    print(f"Avg response time  : {summary['avg_response_ms']} ms "
          f"(median {summary['median_response_ms']}, p95 {summary['p95_response_ms']})")
    print(f"Malformed lines    : {bad_lines}")

    print("\nStatus code distribution:")
    for code, count in summary["status_codes"].items():
        bar = "#" * int(count / summary["total_requests"] * 100)
        print(f"  {code}  {count:>5}  {bar}")

    print("\nPer-endpoint health:")
    print(f"  {'Endpoint':<16}{'Reqs':>6}{'Err%':>8}{'Avg ms':>9}{'P95 ms':>9}  Status")
    print("  " + "-" * 62)
    for r in results:
        print(f"  {r['endpoint']:<16}{r['requests']:>6}{r['error_rate']:>8}"
              f"{r['avg_ms']:>9}{r['p95_ms']:>9}  {r['status']}")

    print(f"\nTop {top_n} most error-prone endpoints:")
    for i, r in enumerate(results[:top_n], 1):
        print(f"  {i}. {r['endpoint']}  ({r['error_rate']}% errors)")

    slow = [e for e in entries if e["rt"] > slow_limit]
    print(f"\nSlow requests (> {slow_limit} ms): {len(slow)}")

    print("\nErrors by hour:")
    for hour, count in summary["errors_by_hour"].items():
        print(f"  {hour}:00  {count}")

    worst = [r for r in results if r["status"] != "HEALTHY"]
    print("\nALERTS:")
    if worst:
        for r in worst:
            print(f"  [{r['status']}] {r['endpoint']} - "
                  f"{r['error_rate']}% errors, avg {r['avg_ms']} ms")
    else:
        print("  All endpoints are healthy.")
    print(line)


def save_reports(summary, results):
    with open("report.json", "w") as f:
        json.dump({"summary": summary, "endpoints": results}, f, indent=4)
    with open("report.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    print("Saved: report.json, report.csv")


# ---------- Main ----------
def main():
    parser = argparse.ArgumentParser(description="API Health Log Analyzer")
    parser.add_argument("--file", default="api_health.log", help="log file path")
    parser.add_argument("--slow", type=int, default=1000, help="slow request limit (ms)")
    parser.add_argument("--top", type=int, default=3, help="how many top error endpoints")
    args = parser.parse_args()

    entries, bad_lines = parse_log(args.file)
    if not entries:
        print("No valid log entries found.")
        return

    results = analyze(entries)
    summary = overall_summary(entries)
    print_report(summary, results, bad_lines, args.slow, args.top, entries)
    save_reports(summary, results)


if __name__ == "__main__":
    main()
