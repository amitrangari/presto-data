import duckdb, time, os
RAW = "/Volumes/4TB/research-data/presto/real-data/squad/RAW_DATA"
OUT = os.path.join(RAW, "aggregated")
con = duckdb.connect()
t0 = time.time()
print(f"[{time.strftime('%H:%M:%S')}] Starting CK aggregation (337GB, non-strict/single-threaded)...", flush=True)
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
print(f"[{time.strftime('%H:%M:%S')}] CK aggregation done in {time.time()-t0:.0f}s", flush=True)
