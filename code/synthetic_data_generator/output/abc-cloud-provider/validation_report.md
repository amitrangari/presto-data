# Validation Report: abc-cloud-provider

**Status:** PASSED
**Generated:** 2026-08-09T05:10:57.023103Z

## Bounds Check: PASS
All metrics within defined bounds.

## Completeness Check: PASS
No missing values detected.

## Correlation Check: PASS (20/21 within tolerance=0.5, pass_rate=95%)

| Metric A | Metric B | Expected | Realized | Deviation | OK |
|----------|----------|----------|----------|-----------|-----|
| System Uptime (%) | Production Deployment Success  | 0.700 | 0.507 | 0.193 | yes |
| System Uptime (%) | Production Monitoring Coverage | 0.600 | 0.395 | 0.205 | yes |
| System Uptime (%) | Test Pass Rate (%) | 0.580 | 0.658 | 0.078 | yes |
| System Uptime (%) | Regression Test Pass Rate (%) | 0.550 | 0.650 | 0.100 | yes |
| System Uptime (%) | Performance SLA Compliance (%) | 0.720 | 0.527 | 0.193 | yes |
| System Uptime (%) | Build Success Rate (%) | 0.550 | 0.386 | 0.164 | yes |
| System Uptime (%) | Build Pipeline Efficiency (%) | 0.480 | 0.359 | 0.121 | yes |
| System Uptime (%) | Resilience Score (1-10) | 0.620 | 0.262 | 0.358 | yes |
| System Uptime (%) | Circuit Breaker Effectiveness  | 0.550 | 0.216 | 0.334 | yes |
| System Uptime (%) | Failover Success Rate (%) | 0.600 | 0.370 | 0.230 | yes |
| System Uptime (%) | Production Environment Health  | 0.650 | 0.425 | 0.225 | yes |
| System Uptime (%) | Performance Baseline Achieveme | 0.500 | 0.444 | 0.056 | yes |
| System Uptime (%) | System Availability (%) | 0.680 | 0.721 | 0.041 | yes |
| System Uptime (%) | SLA Compliance Rate (%) | 0.600 | 0.473 | 0.127 | yes |
| System Uptime (%) | Change Failure Rate (%) | -0.650 | -0.181 | 0.469 | yes |
| System Uptime (%) | Defect Leakage (%) | -0.550 | -0.096 | 0.454 | yes |
| System Uptime (%) | Rollback Rate (%) | -0.500 | -0.307 | 0.193 | yes |
| System Uptime (%) | Production Incident Count | -0.600 | -0.177 | 0.423 | yes |
| System Uptime (%) | Mean Time to Recovery (MTTR) ( | -0.580 | 0.022 | 0.602 | NO |
| System Uptime (%) | Error Rate (%) | -0.520 | -0.202 | 0.318 | yes |
| System Uptime (%) | Error Budget Consumption (%) | -0.450 | -0.247 | 0.203 | yes |
