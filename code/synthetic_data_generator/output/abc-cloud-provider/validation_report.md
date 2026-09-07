# Validation Report: abc-cloud-provider

**Status:** PASSED
**Generated:** 2026-09-07T23:06:01.315715Z

## Bounds Check: PASS
All metrics within defined bounds.

## Completeness Check: PASS
No missing values detected.

## Correlation Check: PASS (20/21 within tolerance=0.5, pass_rate=95%)

| Metric A | Metric B | Expected | Realized | Deviation | OK |
|----------|----------|----------|----------|-----------|-----|
| System Uptime (%) | Production Deployment Success  | 0.700 | 0.502 | 0.198 | yes |
| System Uptime (%) | Production Monitoring Coverage | 0.600 | 0.290 | 0.310 | yes |
| System Uptime (%) | Test Pass Rate (%) | 0.580 | 0.651 | 0.071 | yes |
| System Uptime (%) | Regression Test Pass Rate (%) | 0.550 | 0.591 | 0.041 | yes |
| System Uptime (%) | Performance SLA Compliance (%) | 0.720 | 0.515 | 0.205 | yes |
| System Uptime (%) | Build Success Rate (%) | 0.550 | 0.405 | 0.145 | yes |
| System Uptime (%) | Build Pipeline Efficiency (%) | 0.480 | 0.309 | 0.171 | yes |
| System Uptime (%) | Resilience Score (1-10) | 0.620 | 0.268 | 0.352 | yes |
| System Uptime (%) | Circuit Breaker Effectiveness  | 0.550 | 0.155 | 0.395 | yes |
| System Uptime (%) | Failover Success Rate (%) | 0.600 | 0.402 | 0.198 | yes |
| System Uptime (%) | Production Environment Health  | 0.650 | 0.304 | 0.346 | yes |
| System Uptime (%) | Performance Baseline Achieveme | 0.500 | 0.428 | 0.072 | yes |
| System Uptime (%) | System Availability (%) | 0.680 | 0.701 | 0.021 | yes |
| System Uptime (%) | SLA Compliance Rate (%) | 0.600 | 0.472 | 0.128 | yes |
| System Uptime (%) | Change Failure Rate (%) | -0.650 | -0.256 | 0.394 | yes |
| System Uptime (%) | Defect Leakage (%) | -0.550 | -0.206 | 0.344 | yes |
| System Uptime (%) | Rollback Rate (%) | -0.500 | -0.325 | 0.175 | yes |
| System Uptime (%) | Production Incident Count | -0.600 | -0.181 | 0.419 | yes |
| System Uptime (%) | Mean Time to Recovery (MTTR) ( | -0.580 | 0.025 | 0.605 | NO |
| System Uptime (%) | Error Rate (%) | -0.520 | -0.171 | 0.349 | yes |
| System Uptime (%) | Error Budget Consumption (%) | -0.450 | -0.197 | 0.253 | yes |
