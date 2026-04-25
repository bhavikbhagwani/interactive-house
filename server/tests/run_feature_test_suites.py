#!/usr/bin/env python3
"""Run extended feature test suites (scenes, speech, RBAC, sensors).

Usage (from ``server/``)::

    python tests/run_feature_test_suites.py
    python tests/run_feature_test_suites.py --no-reports   # print only, no files
    python tests/run_feature_test_suites.py --reports-dir ~/Documents/test_results

**Default output directory:** ``server/tests/reports/``

After each run (unless ``--no-reports``) results are saved there (or under
``--reports-dir``):

* ``latest.json`` — machine-readable (counts, duration, per-suite status)
* ``latest.md``  — summary table for documentation / README
* ``run_<timestamp>.json`` — archived copy of ``latest.json``
* ``run_<timestamp>_transcript.txt`` — full console output of every suite

Also runs: ``test_rbac/test_device_access.py`` and
``test_integration/test_server_iter4_wiring.py`` (the latter may fail to
import without ``bcrypt``; that is recorded in the report).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

_SERVER_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DEFAULT_REPORTS_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "reports"
)


def _parse_summary(stdout: str, stderr: str) -> Dict[str, Any]:
    """Parse our test scripts' summary lines. Returns pass/fail/skip/total or nulls."""
    text = stdout + "\n" + stderr
    out: Dict[str, Any] = {
        "passed": None,
        "failed": None,
        "skipped": None,
        "total": None,
    }
    m = re.search(
        r"Summary:\s*(\d+)\s+passed,\s*(\d+)\s+failed,\s*(\d+)\s+skipped of\s*(\d+)",
        text,
    )
    if m:
        out["passed"] = int(m.group(1))
        out["failed"] = int(m.group(2))
        out["skipped"] = int(m.group(3))
        out["total"] = int(m.group(4))
        return out
    m2 = re.search(r"Summary:\s*(\d+)\s*/\s*(\d+)\s*tests passed", text)
    if m2:
        passed, total = int(m2.group(1)), int(m2.group(2))
        out["passed"] = passed
        out["total"] = total
        out["failed"] = max(0, total - passed)
        out["skipped"] = 0
        return out
    return out


def _format_md_table(
    run_id: str,
    rows: List[Dict[str, Any]],
    total_duration_s: float,
    totals: Dict[str, int],
) -> str:
    lines = [
        "# Feature test run metrics",
        "",
        f"- **When (UTC)**: {run_id}",
        f"- **Total wall time (s)**: {total_duration_s:.2f}",
        "",
        "| Suite | Passed | Failed | Skipped | Total | Duration (s) | Status |",
        "|-------|--------|--------|---------|-------|----------------|--------|",
    ]
    for r in rows:
        d = r.get("duration_s")
        ds = f"{d:.2f}" if isinstance(d, (int, float)) else "—"
        st = r.get("status", "ok")
        script = r.get("script", "")
        p, f, sk, tot = r.get("passed"), r.get("failed"), r.get("skipped"), r.get("total")
        if p is None:
            p, f, sk, tot = "—", "—", "—", "—"
        lines.append(
            f"| `{script}` | {p} | {f} | {sk} | {tot} | {ds} | {st} |"
        )
    lines.append("")
    lines.extend(
        [
            "## Aggregates (parsed summaries only)",
            "",
            f"- **Cases passed**: {totals.get('cases_passed', 0)}",
            f"- **Cases failed**: {totals.get('cases_failed', 0)}",
            f"- **Cases skipped**: {totals.get('cases_skipped', 0)}",
            f"- **Cases total**: {totals.get('cases_total', 0)}",
            "",
        ]
    )
    lines.append(
        "Status: **ok** = summary line parsed; **import_error** = dependency/import "
        "failure; **no_summary** = run finished but no `Summary:` line matched; "
        "**exit_nonzero** = process exited with an error; **missing** = file not found."
    )
    return "\n".join(lines) + "\n"


def _run_one(rel_path: str) -> tuple[str, str, int, float]:
    """Run one test file; return stdout, stderr, returncode, duration_s."""
    full = os.path.join(_SERVER_DIR, rel_path)
    env = os.environ.copy()
    env["PYTHONPATH"] = _SERVER_DIR + os.pathsep + env.get("PYTHONPATH", "")
    t0 = time.perf_counter()
    r = subprocess.run(
        [sys.executable, full],
        cwd=_SERVER_DIR,
        capture_output=True,
        text=True,
        env=env,
    )
    dur = time.perf_counter() - t0
    return (r.stdout or ""), (r.stderr or ""), r.returncode, dur


def main() -> None:
    parser = argparse.ArgumentParser(description="Run feature test suites and optional reports.")
    parser.add_argument(
        "--no-reports",
        action="store_true",
        help="Do not write any report files (print to terminal only).",
    )
    parser.add_argument(
        "--reports-dir",
        type=str,
        default=None,
        metavar="DIR",
        help="Where to write latest.json, latest.md, run_*.json, and transcript. "
        f"Default: {_DEFAULT_REPORTS_DIR}",
    )
    args = parser.parse_args()
    reports_dir = os.path.abspath(
        os.path.expanduser(args.reports_dir or _DEFAULT_REPORTS_DIR)
    )

    os.chdir(_SERVER_DIR)
    scripts = [
        "tests/test_scenes/test_scenes_extended.py",
        "tests/test_speech_to_text/test_speech_to_text_extended.py",
        "tests/test_rbac/test_rbac_extended.py",
        "tests/test_rbac/test_device_access.py",
        "tests/test_sensors_automation/test_sensors_automation_extended.py",
        "tests/test_sensors_automation/test_temperature_smoke_rules.py",
        "tests/test_integration/test_server_iter4_wiring.py",
    ]
    run_id = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    ts_file = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    rows: List[Dict[str, Any]] = []
    t_wall0 = time.perf_counter()
    transcript_parts: List[str] = []

    for rel in scripts:
        p = os.path.join(_SERVER_DIR, rel)
        if not os.path.isfile(p):
            print("Missing:", p)
            transcript_parts.append(
                f"\n[MISSING FILE] {rel}\n"
            )
            rows.append(
                {
                    "script": rel,
                    "status": "missing",
                    "duration_s": 0.0,
                }
            )
            continue
        block_hdr = "\n" + "=" * 72 + "\n" + rel + "\n" + "=" * 72 + "\n"
        print(block_hdr, end="")
        out, err, code, dur = _run_one(rel)
        print(out, end="")
        if err:
            print(err, end="", file=sys.stderr)
        transcript_parts.append(block_hdr)
        transcript_parts.append(out)
        if err:
            transcript_parts.append("--- stderr ---\n" + err)

        combined = out + err
        parsed = _parse_summary(out, err)
        if "ModuleNotFoundError" in combined or (
            "ImportError" in combined and "Traceback" in combined
        ):
            st = "import_error"
        elif code != 0:
            st = "exit_nonzero"
        elif parsed.get("passed") is None:
            st = "no_summary"
        else:
            st = "ok"

        row: Dict[str, Any] = {
            "script": rel,
            "returncode": code,
            "duration_s": round(dur, 4),
            "status": st,
        }
        for k in ("passed", "failed", "skipped", "total"):
            if k in parsed and parsed[k] is not None:
                row[k] = parsed[k]
        rows.append(row)

    total_wall = time.perf_counter() - t_wall0

    print("\n" + "=" * 72)
    print("All feature test suites finished (see summaries above).")
    print("=" * 72)

    if not args.no_reports:
        os.makedirs(reports_dir, exist_ok=True)
        tp = tf = tsk = tt = 0
        for r in rows:
            if r.get("passed") is not None:
                tp += int(r.get("passed") or 0)
                tf += int(r.get("failed") or 0)
                tsk += int(r.get("skipped") or 0)
                tt += int(r.get("total") or 0)
        payload = {
            "run_utc": run_id,
            "python": sys.executable,
            "total_duration_s": round(total_wall, 4),
            "totals": {
                "cases_passed": tp,
                "cases_failed": tf,
                "cases_skipped": tsk,
                "cases_total": tt,
            },
            "suites": rows,
        }
        latest_json = os.path.join(reports_dir, "latest.json")
        with open(latest_json, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        snap = os.path.join(reports_dir, f"run_{ts_file}.json")
        with open(snap, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)
        md_path = os.path.join(reports_dir, "latest.md")
        md = _format_md_table(
            run_id,
            rows,
            total_wall,
            payload["totals"],
        )
        with open(md_path, "w", encoding="utf-8") as fh:
            fh.write(md)
        transcript_path = os.path.join(reports_dir, f"run_{ts_file}_transcript.txt")
        with open(transcript_path, "w", encoding="utf-8") as fh:
            fh.write(f"Test run {run_id} (python {sys.executable})\n")
            fh.write(f"Total wall time (s): {round(total_wall, 4)}\n\n")
            fh.write("".join(transcript_parts))
        print(
            f"\nResults saved under:\n  {reports_dir}/\n"
            f"  - latest.json\n  - latest.md\n"
            f"  - {os.path.basename(snap)}\n"
            f"  - {os.path.basename(transcript_path)}\n"
        )


if __name__ == "__main__":
    main()
