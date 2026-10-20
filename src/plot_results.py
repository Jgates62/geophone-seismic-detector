"""
Render logged geophone recordings to a standalone SVG for the README.

Each recording is drawn as a band-passed ("Filtered") trace in millivolts, with the
window where the operator held Shift (Event_Flag == 1) shaded. No plotting library is
required; the SVG is written directly.

Usage:
    python src/plot_results.py [log1.csv log2.csv ...] [-o docs/results.svg]
"""
import argparse
import os
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd

DEFAULT_LOGS = [
    "src/seismic_data_2026-04-21_08-35-03.csv",
    "src/seismic_data_2026-04-21_08-43-03.csv",
]

WIDTH = 900
MARGIN_L, MARGIN_R = 70, 20
PANEL_H = 190
PANEL_GAP = 55
TOP = 66
Y_LIM_MV = 4.0

INK = "#24292f"
MUTED = "#6e7781"
GRID = "#d8dee4"
SIGNAL = "#1f6feb"
EVENT = "#f59e0b"


def load_log(path):
    """Load a logger CSV, dropping rows garbled by serial-read glitches."""
    df = pd.read_csv(path)
    ts = pd.to_datetime(df["UTC_Timestamp"], format="ISO8601")
    df["t"] = (ts - ts.iloc[0]).dt.total_seconds()
    df["mv"] = pd.to_numeric(df["Filtered"], errors="coerce") * 1e3
    df["event"] = pd.to_numeric(df["Event_Flag"], errors="coerce").fillna(0).astype(int)
    return df.dropna(subset=["mv"]).reset_index(drop=True)


def rms(x):
    return float(np.sqrt(np.mean(np.square(x))))


def event_spans(df):
    """Yield (start_s, end_s) for each contiguous run of Event_Flag == 1."""
    run = (df["event"].diff().fillna(0) != 0).cumsum()
    for _, g in df.groupby(run):
        if g["event"].iloc[0] == 1:
            yield g["t"].iloc[0], g["t"].iloc[-1]


def panel(df, title, y0, t_max):
    plot_w = WIDTH - MARGIN_L - MARGIN_R
    sx = lambda t: MARGIN_L + t / t_max * plot_w
    sy = lambda v: y0 + PANEL_H / 2 - v / Y_LIM_MV * (PANEL_H / 2)
    out = [f'<text x="{MARGIN_L}" y="{y0 - 12}" font-size="14" font-weight="600" fill="{INK}">{escape(title)}</text>']

    for a, b in event_spans(df):
        out.append(f'<rect x="{sx(a):.1f}" y="{y0}" width="{sx(b) - sx(a):.1f}" height="{PANEL_H}" fill="{EVENT}" opacity="0.18"/>')

    for v in range(-int(Y_LIM_MV), int(Y_LIM_MV) + 1, 2):
        out.append(f'<line x1="{MARGIN_L}" x2="{WIDTH - MARGIN_R}" y1="{sy(v):.1f}" y2="{sy(v):.1f}" stroke="{GRID}" stroke-width="{1.2 if v == 0 else 0.6}"/>')
        out.append(f'<text x="{MARGIN_L - 8}" y="{sy(v) + 4:.1f}" font-size="11" text-anchor="end" fill="{MUTED}">{v}</text>')
    for s in range(0, int(t_max) + 1):
        out.append(f'<line x1="{sx(s):.1f}" x2="{sx(s):.1f}" y1="{y0 + PANEL_H}" y2="{y0 + PANEL_H + 4}" stroke="{MUTED}"/>')
        out.append(f'<text x="{sx(s):.1f}" y="{y0 + PANEL_H + 17}" font-size="11" text-anchor="middle" fill="{MUTED}">{s}</text>')
    out.append(f'<text x="{MARGIN_L - 48}" y="{y0 + PANEL_H / 2}" font-size="11" fill="{MUTED}" text-anchor="middle" transform="rotate(-90 {MARGIN_L - 48} {y0 + PANEL_H / 2})">Filtered (mV)</text>')

    pts = " ".join(f"{sx(t):.1f},{sy(float(np.clip(v, -Y_LIM_MV, Y_LIM_MV))):.1f}" for t, v in zip(df["t"], df["mv"]))
    out.append(f'<polyline points="{pts}" fill="none" stroke="{SIGNAL}" stroke-width="0.7" stroke-linejoin="round"/>')

    quiet, active = df.loc[df["event"] == 0, "mv"], df.loc[df["event"] == 1, "mv"]
    if len(active) and len(quiet):
        q, e = rms(quiet), rms(active)
        label = f"RMS: {q:.3f} mV quiet → {e:.3f} mV event ({e / q:.0f}×)"
        out.append(f'<text x="{WIDTH - MARGIN_R}" y="{y0 - 12}" font-size="12" text-anchor="end" fill="{INK}">{label}</text>')
    return "\n".join(out)


def build_svg(logs):
    frames = [(os.path.basename(p), load_log(p)) for p in logs]
    t_max = max(df["t"].iloc[-1] for _, df in frames)
    height = TOP + len(frames) * (PANEL_H + PANEL_GAP) + 10
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {height}" font-family="-apple-system, Segoe UI, Helvetica, Arial, sans-serif">',
        f'<rect width="{WIDTH}" height="{height}" fill="#ffffff"/>',
        f'<text x="{MARGIN_L}" y="22" font-size="16" font-weight="700" fill="{INK}">Geophone response during flagged events</text>',
        f'<rect x="{WIDTH - 230}" y="12" width="14" height="10" fill="{EVENT}" opacity="0.35"/>',
        f'<text x="{WIDTH - 211}" y="21" font-size="12" fill="{MUTED}">Shift held (Event_Flag = 1)</text>',
    ]
    for i, (name, df) in enumerate(frames):
        parts.append(panel(df, name, TOP + i * (PANEL_H + PANEL_GAP), t_max))
    last_y = TOP + (len(frames) - 1) * (PANEL_H + PANEL_GAP) + PANEL_H
    parts.append(f'<text x="{(MARGIN_L + WIDTH - MARGIN_R) / 2}" y="{last_y + 36}" font-size="11" text-anchor="middle" fill="{MUTED}">Time since start of recording (s)</text>')
    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("logs", nargs="*", default=DEFAULT_LOGS, help="logger CSV files")
    ap.add_argument("-o", "--output", default="docs/results.svg")
    args = ap.parse_args()

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(build_svg(args.logs))
    print(f"Wrote {args.output}")
