#!/usr/bin/env python3
"""
Core Web Vitals Visual Report Generator

Usage:
  python3 visualize.py --lcp 2.1 --inp 180 --cls 0.05
  python3 visualize.py --lighthouse report.json
  python3 visualize.py --lcp 1.8 --inp 95 --cls 0.02 --url https://example.com --output report.html
"""

import argparse
import json
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

METRICS = {
    "lcp": {
        "name": "LCP",
        "full": "Largest Contentful Paint",
        "desc": "How fast the main content loads",
        "unit": "s",
        "good": 2.5,
        "ni": 4.0,
        "scale": 6.0,
        "fmt": lambda v: f"{v:.2f} s",
    },
    "inp": {
        "name": "INP",
        "full": "Interaction to Next Paint",
        "desc": "How fast the page responds to interactions",
        "unit": "ms",
        "good": 200,
        "ni": 500,
        "scale": 700,
        "fmt": lambda v: f"{int(v)} ms",
    },
    "cls": {
        "name": "CLS",
        "full": "Cumulative Layout Shift",
        "desc": "How stable the layout is while loading",
        "unit": "",
        "good": 0.1,
        "ni": 0.25,
        "scale": 0.35,
        "fmt": lambda v: f"{v:.3f}",
    },
}

COLORS = {
    "good": "#0CCE6B",
    "needs-improvement": "#FFA400",
    "poor": "#FF4E42",
}

LABELS = {
    "good": "Good",
    "needs-improvement": "Needs Improvement",
    "poor": "Poor",
}


def get_rating(key, value):
    m = METRICS[key]
    if value <= m["good"]:
        return "good"
    if value <= m["ni"]:
        return "needs-improvement"
    return "poor"


def pct(key, value):
    return min(100, round((value / METRICS[key]["scale"]) * 100))


def zone_pct(key, threshold):
    return round((threshold / METRICS[key]["scale"]) * 100)


def card_html(key, value):
    m = METRICS[key]
    rating = get_rating(key, value)
    color = COLORS[rating]
    marker_left = pct(key, value)
    good_w = zone_pct(key, m["good"])
    ni_w = zone_pct(key, m["ni"]) - good_w
    poor_w = 100 - good_w - ni_w

    return f"""
    <div class="card" style="border-top:4px solid {color}">
      <div class="card-top">
        <span class="metric-name">{m["name"]}</span>
        <span class="badge" style="background:{color}">{LABELS[rating]}</span>
      </div>
      <div class="metric-full">{m["full"]}</div>
      <div class="metric-desc">{m["desc"]}</div>
      <div class="value" style="color:{color}">{m["fmt"](value)}</div>
      <div class="bar-wrap">
        <div class="bar-track">
          <div class="zone" style="width:{good_w}%;background:{COLORS['good']}30"></div>
          <div class="zone" style="width:{ni_w}%;background:{COLORS['needs-improvement']}30"></div>
          <div class="zone" style="width:{poor_w}%;background:{COLORS['poor']}30"></div>
        </div>
        <div class="marker" style="left:{marker_left}%;background:{color}"></div>
      </div>
      <div class="thresholds">
        <span style="color:{COLORS['good']}">&#9679; Good ≤ {m["fmt"](m["good"])}</span>
        <span style="color:{COLORS['needs-improvement']}">&#9679; NI ≤ {m["fmt"](m["ni"])}</span>
        <span style="color:{COLORS['poor']}">&#9679; Poor > {m["fmt"](m["ni"])}</span>
      </div>
    </div>"""


def generate_report(url, lcp, inp, cls_, generated_at):
    values = {"lcp": lcp, "inp": inp, "cls": cls_}
    present = {k: v for k, v in values.items() if v is not None}
    ratings = {k: get_rating(k, v) for k, v in present.items()}

    all_good = all(r == "good" for r in ratings.values())
    any_poor = any(r == "poor" for r in ratings.values())
    overall_label = "PASS" if all_good else ("FAIL" if any_poor else "NEEDS IMPROVEMENT")
    overall_color = COLORS["good"] if all_good else (COLORS["poor"] if any_poor else COLORS["needs-improvement"])

    cards = "\n".join(card_html(k, v) for k, v in present.items())
    url_line = f'<p class="url">{url}</p>' if url else ""

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>Core Web Vitals Report</title>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#f4f4f5;color:#18181b}}
    header{{background:#fff;border-bottom:1px solid #e4e4e7;padding:24px 32px}}
    h1{{font-size:20px;font-weight:700;color:#09090b}}
    .url{{font-size:13px;color:#71717a;margin-top:4px;word-break:break-all}}
    .meta{{font-size:12px;color:#a1a1aa;margin-top:3px}}
    .overall{{display:inline-flex;align-items:center;gap:6px;margin-top:12px;padding:5px 14px;border-radius:999px;font-size:13px;font-weight:700;color:#fff}}
    .grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:16px;padding:28px 32px;max-width:1050px;margin:0 auto}}
    .card{{background:#fff;border-radius:10px;padding:22px;box-shadow:0 1px 3px rgba(0,0,0,.07)}}
    .card-top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:3px}}
    .metric-name{{font-size:22px;font-weight:800;letter-spacing:-.5px}}
    .badge{{font-size:10px;font-weight:700;letter-spacing:.4px;color:#fff;padding:3px 9px;border-radius:999px}}
    .metric-full{{font-size:12px;color:#52525b;margin-bottom:2px}}
    .metric-desc{{font-size:11px;color:#a1a1aa;margin-bottom:16px}}
    .value{{font-size:42px;font-weight:800;letter-spacing:-1.5px;line-height:1;margin-bottom:18px}}
    .bar-wrap{{position:relative;height:12px;margin-bottom:12px}}
    .bar-track{{display:flex;width:100%;height:8px;border-radius:4px;overflow:hidden;margin-top:2px}}
    .zone{{height:100%}}
    .marker{{position:absolute;top:50%;transform:translate(-50%,-50%);width:14px;height:14px;border-radius:50%;border:3px solid #fff;box-shadow:0 1px 4px rgba(0,0,0,.25)}}
    .thresholds{{display:flex;gap:10px;flex-wrap:wrap;font-size:11px}}
    footer{{text-align:center;padding:20px;font-size:12px;color:#d4d4d8}}
  </style>
</head>
<body>
  <header>
    <h1>Core Web Vitals Report</h1>
    {url_line}
    <p class="meta">Generated: {generated_at}</p>
    <div class="overall" style="background:{overall_color}">{overall_label}</div>
  </header>
  <div class="grid">
    {cards}
  </div>
  <footer>Generated by ts-dev-kit &middot; core-web-vitals skill</footer>
</body>
</html>"""


def parse_lighthouse(path):
    with open(path) as f:
        data = json.load(f)
    url = data.get("finalUrl") or data.get("requestedUrl") or ""
    audits = data.get("audits", {})
    lcp_ms = (audits.get("largest-contentful-paint") or {}).get("numericValue")
    inp_ms = (audits.get("interaction-to-next-paint") or {}).get("numericValue")
    cls = (audits.get("cumulative-layout-shift") or {}).get("numericValue")
    lcp = lcp_ms / 1000 if lcp_ms is not None else None
    return url, lcp, inp_ms, cls


def main():
    p = argparse.ArgumentParser(description="Generate a Core Web Vitals HTML report")
    p.add_argument("--lcp", type=float, help="LCP in seconds (e.g. 2.1)")
    p.add_argument("--inp", type=float, help="INP in milliseconds (e.g. 180)")
    p.add_argument("--cls", type=float, help="CLS score (e.g. 0.05)")
    p.add_argument("--lighthouse", help="Path to a Lighthouse JSON output file")
    p.add_argument("--url", help="URL that was tested (display only)")
    p.add_argument("--output", default="cwv-report.html", help="Output HTML file path")
    p.add_argument("--no-open", action="store_true", help="Do not open in browser")
    args = p.parse_args()

    url = args.url or ""
    lcp, inp, cls_ = args.lcp, args.inp, args.cls

    if args.lighthouse:
        lh_url, lh_lcp, lh_inp, lh_cls = parse_lighthouse(args.lighthouse)
        url = url or lh_url
        lcp = lcp if lcp is not None else lh_lcp
        inp = inp if inp is not None else lh_inp
        cls_ = cls_ if cls_ is not None else lh_cls

    if lcp is None and inp is None and cls_ is None:
        print("Error: no metrics provided.", file=sys.stderr)
        print("Usage: visualize.py --lcp 2.1 --inp 180 --cls 0.05", file=sys.stderr)
        print("       visualize.py --lighthouse report.json", file=sys.stderr)
        sys.exit(1)

    html = generate_report(url, lcp, inp, cls_, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    out = Path(args.output)
    out.write_text(html, encoding="utf-8")
    print(f"Report saved to {out.resolve()}")

    if not args.no_open:
        webbrowser.open(out.resolve().as_uri())


if __name__ == "__main__":
    main()
