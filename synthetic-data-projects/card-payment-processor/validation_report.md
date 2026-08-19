# Validation Report: card-payment-processor

**Status:** PASSED
**Generated:** 2026-08-09T03:55:00.696808Z

## Bounds Check: PASS
All metrics within defined bounds.

## Completeness Check: PASS
No missing values detected.

## Correlation Check: PASS (17/21 within tolerance=0.5, pass_rate=81%)

| Metric A | Metric B | Expected | Realized | Deviation | OK |
|----------|----------|----------|----------|-----------|-----|
| System Uptime (%) | Production Deployment Success  | 0.700 | 0.415 | 0.285 | yes |
| System Uptime (%) | Production Monitoring Coverage | 0.600 | 0.521 | 0.079 | yes |
| System Uptime (%) | Test Pass Rate (%) | 0.580 | 0.683 | 0.103 | yes |
| System Uptime (%) | Regression Test Pass Rate (%) | 0.550 | 0.671 | 0.121 | yes |
| System Uptime (%) | Performance SLA Compliance (%) | 0.720 | 0.469 | 0.251 | yes |
| System Uptime (%) | Build Success Rate (%) | 0.550 | 0.149 | 0.401 | yes |
| System Uptime (%) | Build Pipeline Efficiency (%) | 0.480 | 0.111 | 0.369 | yes |
| System Uptime (%) | Resilience Score (1-10) | 0.620 | 0.224 | 0.396 | yes |
| System Uptime (%) | Circuit Breaker Effectiveness  | 0.550 | 0.274 | 0.276 | yes |
| System Uptime (%) | Failover Success Rate (%) | 0.600 | 0.471 | 0.129 | yes |
| System Uptime (%) | Production Environment Health  | 0.650 | 0.215 | 0.435 | yes |
| System Uptime (%) | Performance Baseline Achieveme | 0.500 | 0.338 | 0.162 | yes |
| System Uptime (%) | System Availability (%) | 0.680 | 0.786 | 0.106 | yes |
| System Uptime (%) | SLA Compliance Rate (%) | 0.600 | 0.457 | 0.143 | yes |
| System Uptime (%) | Change Failure Rate (%) | -0.650 | -0.035 | 0.615 | NO |
| System Uptime (%) | Defect Leakage (%) | -0.550 | -0.020 | 0.530 | NO |
| System Uptime (%) | Rollback Rate (%) | -0.500 | -0.293 | 0.207 | yes |
| System Uptime (%) | Production Incident Count | -0.600 | -0.184 | 0.416 | yes |
| System Uptime (%) | Mean Time to Recovery (MTTR) ( | -0.580 | -0.007 | 0.573 | NO |
| System Uptime (%) | Error Rate (%) | -0.520 | 0.089 | 0.609 | NO |
| System Uptime (%) | Error Budget Consumption (%) | -0.450 | -0.192 | 0.258 | yes |
