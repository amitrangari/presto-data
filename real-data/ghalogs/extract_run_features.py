#!/usr/bin/env python3
"""Stream runs.json.gz once, extracting per-run build/test timing aggregates.

GHALogs' value-add over TravisTorrent is per-step timing (build vs. test vs. setup separated,
not a single tr_duration). This script classifies each logged step by simple keyword heuristics
into build/test/setup/other and aggregates to one row per run, then writes a compact CSV so the
downstream pipeline script doesn't need to re-parse the 1GB+ JSON on every run.
"""
import gzip
import json
import re
import sys
from pathlib import Path

import csv

SCRIPT_DIR = Path(__file__).resolve().parent
RUNS_PATH = SCRIPT_DIR / "runs.json.gz"
OUT_PATH = SCRIPT_DIR / "run_features.csv"

TEST_RE = re.compile(r"\btest|pytest|jest|mocha|unittest|junit|rspec|cargo test|go test|gradle test|mvn test|karma|cypress|playwright\b", re.I)
BUILD_RE = re.compile(r"\bbuild|compile|webpack|rollup|tsc|make|cmake|gradle build|maven|mvn package|docker build|setup-|cache\b", re.I)


def classify(step: dict) -> str:
    parts = []
    if step.get("action"):
        parts.append(step["action"])
    if step.get("code"):
        parts.append(step["code"])
    if step.get("categories"):
        parts.append(" ".join(step.get("categories", [])))
    commands = step.get("commands", [])
    for c in commands:
        if isinstance(c, dict):
            parts.append(c.get("command", ""))
            parts.extend(str(cat) for cat in c.get("categories", []))
    text = " ".join(str(p) for p in parts)
    if TEST_RE.search(text):
        return "test"
    if BUILD_RE.search(text):
        return "build"
    return "other"


def main():
    n = 0
    written = 0
    with gzip.open(RUNS_PATH, "rt") as fin, open(OUT_PATH, "w", newline="") as fout:
        writer = csv.writer(fout)
        writer.writerow([
            "repository_name", "workflow_path", "run_number", "run_attempt",
            "conclusion", "created_at", "run_started_at", "updated_at",
            "n_steps", "build_time_sec", "test_time_sec", "setup_time_sec", "other_time_sec",
            "total_step_time_sec",
        ])
        for line in fin:
            n += 1
            if n % 50000 == 0:
                print(f"  processed {n} runs, written {written}", file=sys.stderr)
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            meta = d.get("metadata", {})
            insights = d.get("log_insights") or []
            build_t = test_t = setup_t = other_t = 0.0
            n_steps = 0
            for job_log in insights:
                for step in job_log.get("steps", []):
                    dur = step.get("duration_sec")
                    if dur is None:
                        continue
                    n_steps += 1
                    cls = classify(step)
                    action = (step.get("action") or "").lower()
                    if cls == "other" and ("checkout" in action or "setup-" in action or "cache" in action):
                        cls = "setup"
                    if cls == "build":
                        build_t += dur
                    elif cls == "test":
                        test_t += dur
                    elif cls == "setup":
                        setup_t += dur
                    else:
                        other_t += dur
            if n_steps == 0:
                continue
            writer.writerow([
                d.get("repository_name"), d.get("workflow_path"), d.get("run_number"), d.get("run_attempt"),
                meta.get("conclusion"), meta.get("created_at"), meta.get("run_started_at"), meta.get("updated_at"),
                n_steps, round(build_t, 3), round(test_t, 3), round(setup_t, 3), round(other_t, 3),
                round(build_t + test_t + setup_t + other_t, 3),
            ])
            written += 1
    print(f"Done. {n} runs read, {written} runs with step timing written to {OUT_PATH}", file=sys.stderr)


if __name__ == "__main__":
    main()
