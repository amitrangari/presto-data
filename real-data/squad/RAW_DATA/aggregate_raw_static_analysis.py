#!/usr/bin/env python3
"""Aggregate SQuaD's raw per-file/per-issue static-analysis dumps (sonarqube.csv,
pmd.csv, ck.csv -- hundreds of GB each) down to one row per (project, release),
using DuckDB's streaming CSV scanner so nothing needs to fit in memory.

Goal: produce code-quality / complexity / defect-density features that map to
PRESTO's registry (Code phase) and that the paper's existing SQuaD validation
(process_metrics.csv: LOC, churn, commit-author count, release age) does not
have -- see the 2026-08-14 SQuaD full-data extraction.
"""
import duckdb
import os
import time

RAW = "/Volumes/4TB/research-data/presto/real-data/squad/RAW_DATA"
OUT = os.path.join(RAW, "aggregated")
os.makedirs(OUT, exist_ok=True)


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


con = duckdb.connect()

# ---------------------------------------------------------------------------
# 1. SonarQube: project-level code-quality "measures_*" columns are repeated
#    on every issue row for the same (project_name, release_name); ANY_VALUE
#    collapses them to one row per project-release. Curated to current-state
#    (non "new_*" delta) metrics that map to PRESTO's Code-phase registry.
# ---------------------------------------------------------------------------
SQ_MEASURES = [
    "measures_bugs", "measures_code_smells", "measures_cognitive_complexity",
    "measures_comment_lines_density", "measures_complexity", "measures_coverage",
    "measures_duplicated_lines_density", "measures_files", "measures_functions",
    "measures_lines", "measures_ncloc", "measures_reliability_rating",
    "measures_security_rating", "measures_security_hotspots",
    "measures_sqale_debt_ratio", "measures_sqale_index", "measures_sqale_rating",
    "measures_violations", "measures_vulnerabilities", "measures_classes",
    "measures_statements", "measures_maintainability_issues_total",
]
sq_select = ", ".join(f"ANY_VALUE({c}) AS {c}" for c in SQ_MEASURES)
log("Starting SonarQube aggregation (179GB, single-threaded due to quoted newlines)...")
t0 = time.time()
try:
    con.execute(f"""
        COPY (
          SELECT project_name, release_name, COUNT(*) AS n_issue_rows, {sq_select}
          FROM read_csv('{RAW}/sonarqube.csv', delim=',', quote='"', escape='"',
                         ignore_errors=true, null_padding=true, max_line_size=10000000,
                         strict_mode=false, parallel=false)
          GROUP BY project_name, release_name
        ) TO '{OUT}/sonarqube_project_release_measures.csv' (HEADER, DELIMITER ',')
    """)
    log(f"SonarQube aggregation done in {time.time()-t0:.0f}s")
except Exception as e:
    log(f"SonarQube aggregation FAILED: {e}")

# ---------------------------------------------------------------------------
# 2. PMD: violation counts per (project, release), by priority (1=highest).
# ---------------------------------------------------------------------------
log("Starting PMD aggregation (678GB)...")
t0 = time.time()
try:
    con.execute(f"""
        COPY (
          SELECT project_name, release_ID,
                 COUNT(*) AS n_violations,
                 SUM(CASE WHEN priority = '1' THEN 1 ELSE 0 END) AS n_priority1,
                 SUM(CASE WHEN priority = '2' THEN 1 ELSE 0 END) AS n_priority2,
                 SUM(CASE WHEN priority = '3' THEN 1 ELSE 0 END) AS n_priority3,
                 SUM(CASE WHEN priority = '4' THEN 1 ELSE 0 END) AS n_priority4,
                 SUM(CASE WHEN priority = '5' THEN 1 ELSE 0 END) AS n_priority5,
                 COUNT(DISTINCT filename) AS n_files_with_violations,
                 COUNT(DISTINCT rule) AS n_distinct_rules
          FROM read_csv('{RAW}/pmd.csv', delim=',', quote='"', escape='"',
                         ignore_errors=true, null_padding=true, max_line_size=10000000)
          GROUP BY project_name, release_ID
        ) TO '{OUT}/pmd_project_release_counts.csv' (HEADER, DELIMITER ',')
    """)
    log(f"PMD aggregation done in {time.time()-t0:.0f}s")
except Exception as e:
    log(f"PMD aggregation FAILED: {e}")

# ---------------------------------------------------------------------------
# 3. CK: average OO/complexity metrics per (project, release), class-level rows.
# ---------------------------------------------------------------------------
log("Starting CK aggregation (337GB)...")
t0 = time.time()
try:
    con.execute(f"""
        COPY (
          SELECT project_name, release,
                 COUNT(*) AS n_class_rows,
                 AVG(TRY_CAST(class_wmc AS DOUBLE)) AS avg_wmc,
                 AVG(TRY_CAST(class_cbo AS DOUBLE)) AS avg_cbo,
                 AVG(TRY_CAST(class_dit AS DOUBLE)) AS avg_dit,
                 AVG(TRY_CAST(class_loc AS DOUBLE)) AS avg_class_loc,
                 AVG(TRY_CAST(class_lcom AS DOUBLE)) AS avg_lcom,
                 AVG(TRY_CAST(class_rfc AS DOUBLE)) AS avg_rfc,
                 AVG(TRY_CAST(class_noc AS DOUBLE)) AS avg_noc
          FROM read_csv('{RAW}/ck.csv', delim=',', quote='"', escape='"',
                         ignore_errors=true, null_padding=true, max_line_size=10000000,
                         strict_mode=false, parallel=false)
          WHERE metric_type = 'class'
          GROUP BY project_name, release
        ) TO '{OUT}/ck_project_release_avg.csv' (HEADER, DELIMITER ',')
    """)
    log(f"CK aggregation done in {time.time()-t0:.0f}s")
except Exception as e:
    log(f"CK aggregation FAILED: {e}")

log("ALL AGGREGATIONS COMPLETE")
