# Real-World SDLC Metrics and Performance Data Catalog

**Compiled for:** PRESTO / "A Machine Learning Framework for Predicting Software System Performance Using SDLC Metrics" (Rangari, Mishra, Nagrare, Nayak)
**Compiled:** 2026-08-08
**Purpose:** Identify real, publicly available datasets and benchmark statistics that can (a) add genuine real-world validation beyond the current TravisTorrent section, (b) harden the DORA calibration claims for the synthetic generator, and (c) strengthen related-work grounding.

***

## 0. Manuscript state check (read before using this catalog)

The task brief described the paper as claiming `R^2 = 0.992` on synthetic data only. **The manuscript at `/Volumes/1TB-SSD/presto/paper-work/overleaf/main_mdpi.tex` no longer says that.** Current state as of this reading:

* Headline result is `R^2 = 0.387` (Gradient Boosting, SDLC-only features, no target leakage). The `0.946` figure is explicitly reported as leakage-inflated, with 71 percent attributed to temporal autocorrelation.
* Target variable is **System Uptime (percent)**, not response time or latency.
* Feature count is 164 raw metrics into 273 engineered features (241 after leakage removal), not 498.
* Section `sec:travistorrent` **already contains a real-world validation** on 7 TravisTorrent projects, target = build duration, best `R^2 = 0.306`, median `R^2 = -0.169`.
* Three synthetic domains: ABC Cloud (170 releases / 5 yr), XYZ Sales Force (200 / 5.5 yr), Card Payment (150 / 4 yr).
* `Table tab:validity` still marks External Validity as **Critical / Unmitigated**.

So the fatal weakness is no longer "zero real data". It is narrower and sharper:

1. **Target mismatch.** The real-world validation predicts *build duration*, a CI-side variable, while the whole framework is pitched at *production uptime*. No real production outcome is ever predicted.
2. **Phase coverage collapse.** TravisTorrent supplies only 4 of 8 SDLC phases. Requirements, UAT, Performance Testing and Chaos Testing, which are 4 of the 8 pillars of the contribution, have zero real grounding.
3. **A falsifiable novelty claim.** Section `sec:synthetic_data` and Section `sec:external_validity` both assert that *no* public dataset combines SDLC process metrics with runtime performance, based on "an exhaustive search of UCI, Kaggle, Zenodo, Papers with Code, TravisTorrent, GHTorrent, PROMISE". **That claim is now wrong, and a reviewer with domain knowledge will find the counterexample in one search.** See item #1 below.

Priorities in this catalog are ordered against those three problems, not the outdated brief.

***

## 1. Top 5 most promising for real-world validation

Ranked by how directly each closes the specific gap above, weighted by acquisition cost.

### #1. Mozilla Performance Measurements and Alerts (ICPE 2025 Data Artifact)

**This is the single highest-value item in this catalog, and it is also the biggest threat to the paper as currently written.**

| Field | Value |
|:--|:--|
| URL | https://doi.org/10.5281/zenodo.14642238 (concept DOI; latest v5 at https://zenodo.org/records/15465568) |
| Paper | Companion of ICPE '25, https://dl.acm.org/doi/10.1145/3680256.3721973 , preprint https://arxiv.org/abs/2503.16332 |
| Group | REALISE Lab, Concordia University |
| Contents | 5,655 performance time series, 17,989 expert-validated performance alerts, linked Bugzilla bug annotations, test metadata (platform, suite, framework, test config) |
| Period | May 2023 to May 2024 |
| Size | 561 MB total. `timeseries-data.zip` 543 MB, `alerts_data.csv` 17.3 MB, `bugs_data.csv` 304 kB, `scripts.zip` 310 kB |
| License | CC-BY-4.0 |
| Source system | Mozilla Treeherder / Perfherder public API |

**Why it matters twice over.**

*As a threat:* This dataset links code pushes to real runtime performance measurements, expert-triaged regression alerts, and the resulting bug reports. It is exactly "a public dataset combining development process data with runtime performance outcomes". It was published in March 2025, it is CC-BY, and it is indexed on arXiv and the ACM DL. The manuscript's "no such benchmark exists in UCI, Kaggle, Zenodo, PROMISE, or any repository we surveyed" statement is directly contradicted by a Zenodo record. Fix the claim before submission: narrow it to "no public dataset links *release-level, multi-phase SDLC process metrics* to *production availability outcomes*", which remains true and defensible.

*As an opportunity:* This is the best available substrate for a second, stronger real-world validation section. Each Perfherder time series is a runtime measurement (page load, speedometer, startup, memory) attached to a specific revision on a specific branch. Joining against the public Treeherder API for the same push IDs yields build/test job outcomes, job durations, retrigger counts and test failure counts, which are genuine Build and Test phase SDLC metrics. That gives a real `SDLC metrics at revision t -> runtime performance at revision t` regression with the same time-series-CV protocol PRESTO already uses. The alerts file gives a second, arguably more useful, target: a binary "did this push trigger a validated performance regression" label, which maps far better onto the paper's release-risk-scoring application than build duration does.

**Concrete use:** replace or augment Section `sec:travistorrent` with a Mozilla study. Target 1: regression on a normalized performance metric. Target 2: classification of alert-triggering pushes. Report both. This converts External Validity from Critical/Unmitigated to Critical/Partially Mitigated with a *runtime* rather than *build-time* target.

***

### #2. SQuaD: The Software Quality Dataset (MSR 2026 submission)

| Field | Value |
|:--|:--|
| URL | https://zenodo.org/records/17566691 , paper https://arxiv.org/abs/2511.11265 |
| Authors | Robredo, Esposito, Taibi, Peñaloza, Lenarduzzi |
| Contents | 450 mature OSS projects (Apache, Mozilla, FFmpeg, Linux kernel). Nine static analysis tools unified: SonarQube, CodeScene, PMD, Understand, CK, JaSoMe, RefactoringMiner, RefactoringMiner++, PyRef. 700+ unique metrics at method / class / file / project level. Plus VCS history, issue tracking history, CVE/CWE vulnerability data, and process metrics validated for JIT defect prediction |
| Scale | 63,586 analyzed project releases |
| Granularity | **Release level**, time-aware |
| License | Open, Zenodo hosted (verify exact CC variant on the record) |

**Why it matters.** This is the closest real analogue to PRESTO's Code phase plus Requirements/Issue phase, at the exact temporal unit PRESTO uses (the release). 63,586 real releases against PRESTO's 520 synthetic ones. It does not contain a runtime performance target, so it cannot validate the end-to-end claim alone. Its value is threefold: (a) it lets you check whether the copula-specified correlations among *code* metrics resemble real inter-metric correlations, which directly answers the "Copula Correlation Specification" internal validity threat; (b) it supplies real marginal distributions to recalibrate Stage 1 of the generator instead of relying on domain expertise; (c) paired with Mozilla and FFmpeg overlap it can be joined to item #1 for the Mozilla subset.

**Concrete use:** a new subsection "Calibrating the generator against real release data". Compare the 84 specified correlation pairs against empirical correlations in SQuaD wherever the metric pair exists. Any pair whose sign or magnitude is contradicted becomes an explicit, reported limitation. This is a cheap, high-credibility addition that reviewers reward.

***

### #3. GHALogs: Large-Scale Dataset of GitHub Actions Runs (MSR 2025)

| Field | Value |
|:--|:--|
| URL | https://doi.org/10.5281/zenodo.10154920 , code and samples https://github.com/D2KLab/gha-dataset |
| Paper | MSR 2025 Data and Tool Showcase, https://2025.msrconf.org/details/msr-2025-data-and-tool-showcase-track/1/GHALogs-Large-scale-dataset-of-GitHub-Actions-runs , PDF https://www.s3.eurecom.fr/docs/msr25_moriconi.pdf |
| Contents | 116k CI/CD workflows, 25k public repositories, 20 languages, 513k workflow runs, 2.3M individual steps, **with full run logs** |
| Size | `repositories.json.gz` + `runs.json.gz` about 1 GB. `github_run_logs.zip` about 142 GB (do not download the logs; the 1 GB metadata is sufficient) |
| Format | gzipped JSON Lines |
| License | Check the Zenodo record; the GitHub README does not state one |

**Why it matters.** TravisTorrent's data stops in 2017 and Travis CI is no longer the dominant OSS CI. A reviewer can reasonably object that the paper's only real validation uses a decade-old snapshot of a deprecated platform. GHALogs is the modern replacement, is 2024/2025 vintage, has per-step timing (so build duration, test step duration, setup duration are separable rather than conflated), and covers 20 languages. Step-level timing is strictly richer than TravisTorrent's single `tr_duration`.

**Concrete use:** either replace the TravisTorrent section with GHALogs or, better, keep TravisTorrent and add GHALogs as a second CI cohort. Being able to write "results replicate across two independent CI platforms a decade apart" is a much stronger external validity statement than either alone. Also note that per-step granularity lets you isolate *test execution* duration from *build* duration, which addresses the paper's own explanation that "build duration is dominated by infrastructure factors".

**Companion dataset:** "A dataset of GitHub Actions workflow histories" (Cardoen, Decan, Mens, MSR 2024), https://doi.org/10.5281/zenodo.10259013 and updated at https://zenodo.org/records/13985548 , 2.3M+ workflows from 43.3K+ repositories. This one is workflow *configuration* history rather than run outcomes, useful for measuring CI process maturity as a feature.

***

### #4. DORA / Accelerate State of DevOps 2024 (calibration evidence, not a dataset)

| Field | Value |
|:--|:--|
| URL | https://dora.dev/research/2024/dora-report/ , also https://research.google/pubs/dora-accelerate-state-of-devops-2024-report/ |
| Contents | Survey of 39,000+ professionals. Four key metrics with cluster boundaries: deployment frequency, lead time for change, change failure rate, failed deployment recovery time |
| 2024 cluster distribution | Elite 19 percent, High 22 percent, Medium 35 percent, Low 25 percent |
| 2024 tier boundaries | Elite: on-demand deploys, lead time under one day, change failure rate around 5 percent, recovery under one hour. High: deploy once per day to once per week. Medium: once per week to once per month. Low: less than once per month |
| Notable 2024 shift | High tier shrank from 31 to 22 percent; Low tier grew from 17 to 25 percent. For the first time the Medium cluster had a *lower* change failure rate than the High cluster |
| Access | Free PDF, no microdata released |

**Why it matters.** The manuscript already cites `dora2024` for generator calibration, but the calibration is asserted rather than shown. The concrete numbers above let you demonstrate it.

**The realism check the reviewers will actually run:** ABC Cloud is specified as 170 releases over 5 years, that is **34 releases per year, roughly one every 10.7 days**. DORA "High" is *once per day to once per week*. 170/5yr is slower than DORA Medium's upper bound and well outside the High band the profile claims. XYZ Sales Force at 200 releases over 5.5 years is 36 per year, same problem, and it is described as "aggressive release cadence". Card Payment at 150 over 4 years is 37.5 per year while claiming DORA **Elite**, which requires on-demand deployment. **All three domain profiles are one to two DORA tiers slower than the tier they are labelled with.** This is a live, checkable inconsistency between Section `sec:synthetic_data` and the cited calibration source.

Two defensible resolutions, pick one and state it explicitly:
* Reframe the temporal unit. If a "release" means a coordinated versioned release train rather than a deployment, say so, and decouple the release count from the DORA deployment-frequency tier. Many DORA-Elite organizations cut major versioned releases monthly while deploying continuously.
* Or regenerate the domains at DORA-consistent cadence. Note this also multiplies sample size, which happens to fix the paper's other big problem (241 features against 136 training rows).

The first option is a paragraph. The second is a rerun. Either beats leaving the arithmetic exposed.

**Supporting citations for the same argument:** Forsgren, Humble, Kim, *Accelerate* (2018), already cited as `forsgren2018`. Prior year reports at https://dora.dev/research/ allow a trend line, which is useful if you want to argue the synthetic cadence reflects a mid-decade enterprise average rather than a 2024 snapshot.

***

### #5. VOID: Verica Open Incident Database

| Field | Value |
|:--|:--|
| URL | https://www.thevoid.community/database , reports at https://www.thevoid.community/ |
| Contents | Community-contributed software incident reports, 10,000+ incidents from nearly 600 companies, Fortune 100 through startups. Duration, description, contributing factors |
| Access | Free, browsable database, registration for the annual report |
| Key finding to cite | Incident duration is heavily positively skewed and long-tailed, so MTTR as a mean is not a reliable central tendency measure. Courtney Nash's analysis: https://www.infoq.com/articles/incident-metrics-void/ |

**Why it matters.** Two distinct uses.

*Distributional calibration.* The generator's Stage 1 uses log-normal marginals for time-based metrics. VOID provides real empirical evidence on the shape of incident duration distributions, letting you cite a real source instead of a modeling convention. It also supports the "shock events with exponential recovery" choice in Stage 3.

*Construct validity defense.* The manuscript's target is System Uptime as a percentage aggregated per release. VOID's central finding, that incident duration distributions are so skewed that means mislead, is directly relevant to whether a per-release uptime percentage is a well-behaved regression target at all. Better to cite this yourself in Section `sec:construct_validity` than to have a reviewer raise it. A uptime percentage over a release window is dominated by whether one long-tail incident happened to land inside the window, which is substantially a Poisson coin flip rather than a function of SDLC quality. This may be the honest explanation for why `R^2` tops out at 0.387.

***

## 2. Mining Software Repositories datasets with SDLC metrics plus outcome variables

### 2.1 SmartSHARK

| Field | Value |
|:--|:--|
| URL | https://smartshark.github.io/ , MSR 2022 mining challenge https://conf.researchr.org/track/msr-2022/msr-2022-mining-challenge , paper https://arxiv.org/abs/2102.11540 , ecosystem paper https://arxiv.org/abs/2001.01606 |
| Contents | Single MongoDB linking: git commits, code metrics (OpenStaticAnalyzer via mecoSHARK), AST node metrics (coastSHARK), code clones, PMD warnings, change types, refactorings, Jira issues (issueSHARK), GitHub pull requests, **and Travis CI data** |
| Scale | 77 open-source Java projects, all Apache ecosystem |
| Key property | Explicit cross-source links: commit to issue, PR to commits, build to commit |
| Access | MongoDB dump, free download |

**Relevance to PRESTO:** the closest existing thing to PRESTO's "multi-source data intake pipeline" contribution. It covers Requirements/Issue, Code, Build and Test phases in one integrated store, which is 4 of the 8 phases with better issue-side coverage than TravisTorrent. **Cite it in Section `sec:ingestion_challenges` and `sec:related_work`.** The paper currently presents multi-source SDLC harmonization as a novel engineering contribution without acknowledging that SmartSHARK solved a large part of this problem in 2020. A reviewer familiar with MSR will notice. Position PRESTO's pipeline as extending SmartSHARK-class integration to production telemetry phases, which is genuinely new.

### 2.2 The Technical Debt Dataset

| Field | Value |
|:--|:--|
| URL | https://github.com/clowee/The-Technical-Debt-Dataset , paper https://arxiv.org/abs/1908.00827 |
| Contents | 78K commits from 33 Java projects. 1.8M SonarQube issues, 62K code smells, 28K faults, 57K refactorings. Fault-inducing and fault-fixing commits identified via SZZ. Jira issue linkage |
| Format | CSV files plus an SQLite database |
| License | Open |

**Relevance:** real pairing of code complexity and quality metrics with fault outcomes. Directly supports category 4 of the brief. Useful as a citation that code-quality-to-defect signal in real projects is real but modest, which contextualizes PRESTO's `R^2 = 0.387` as unremarkable rather than disappointing. See also the derived ESE paper: Lenarduzzi et al., "A machine and deep learning analysis among SonarQube rules, product, and process metrics for fault prediction", https://link.springer.com/article/10.1007/s10664-022-10164-z , which reports realistic accuracy ceilings for exactly this kind of prediction.

### 2.3 The Public Jira Dataset

| Field | Value |
|:--|:--|
| URL | https://zenodo.org/doi/10.5281/zenodo.5882881 (concept DOI, v7 as of June 2025) , paper https://arxiv.org/abs/2201.08368 |
| Authors | Montgomery, Lüders, Maalej (MSR 2022) |
| Contents | 16 public Jira instances, 1,822 projects, **2.7M issues**, 32M changes, 9M comments, 1M issue links. Anonymized user records |
| Format | MongoDB dump plus download and interpretation scripts |

**Relevance:** the only realistic public source for PRESTO's **Requirements phase**, which is currently one of the four phases with zero real grounding. Requirements stability, issue churn, scope change rate, priority distribution and time-to-triage are all derivable at release granularity. Combine with SmartSHARK or SQuaD for Apache projects present in both.

### 2.4 20-MAD (20 Years of Mozilla and Apache Development)

| Field | Value |
|:--|:--|
| URL | https://arxiv.org/abs/2003.14015 , MSR 2020 data showcase |
| Contents | 765 projects, 3.4M commits, 2.3M issues, 17.3M issue comments, spanning 20+ years. Commit-issue linkage. Comments pre-processed for NLP and sentiment (valence, arousal) |
| Size | 6+ GB compressed |

**Relevance:** long-horizon release history for Mozilla projects, which makes it a natural join partner for item #1. If you go the Mozilla route, 20-MAD supplies the historical Code and Issue phase context that the one-year Perfherder window lacks.

### 2.5 SEART GitHub Search (GHS)

| Field | Value |
|:--|:--|
| URL | https://seart-ghs.si.usi.ch/ , code https://github.com/seart-group/ghs , paper https://arxiv.org/abs/2103.04682 , Data Hub https://arxiv.org/abs/2409.18658 |
| Contents | 735,669 GitHub repositories in 10 languages, 25 mined characteristics each, continuously updated. Commits, issues, contributors, stars, license, fork status |
| Constraint | Only repositories with 10+ stars are mined |

**Relevance:** sampling frame, not an outcome dataset. Use it to justify project selection in any new real-world validation, which is a methodological point ESE and MDPI reviewers care about. The current TravisTorrent section says "we selected 7 diverse projects" with no stated sampling protocol; that is a soft target. GHS lets you state explicit inclusion criteria.

### 2.6 GHTorrent (status warning)

| Field | Value |
|:--|:--|
| URL | https://ghtorrent.org/ |
| Status | **Effectively unmaintained.** Data collection wound down; MySQL dumps and the streaming service are no longer reliably updated |

The manuscript cites GHTorrent in Section `sec:synthetic_data` as part of its exhaustive search. Keep the citation but do not propose it as a validation source; a reviewer will know it is stale. Prefer SEART GHS or the GH Archive derived datasets.

### 2.7 Index resources worth checking for anything missed

* **awesome-msr**, https://github.com/dspinellis/awesome-msr , curated list of SE repository mining datasets
* **Directory of MSR Datasets**, https://authecesofteng.github.io/directory-msr-datasets/ , metadata, citations and evaluation for MSR data showcase artifacts
* **MSR Data and Tool Showcase tracks**, https://2024.msrconf.org/track/msr-2024-data-and-tool-showcase-track and the 2025 / 2026 equivalents

***

## 3. CI/CD build metrics and flaky test datasets

### 3.1 TravisTorrent (currently used by the paper)

| Field | Value |
|:--|:--|
| URL | https://travistorrent.testroots.org/ , site https://testroots.github.io/travistorrent-site/ , archived on Figshare https://figshare.com/articles/dataset/TravisTorrent/19314170 |
| Contents | 2.64M Travis CI builds from 1,359 GitHub projects. Build duration, status, test counts, test duration, source churn, SLOC, files modified, team size, repo age, commit counts |
| Status | Last substantive update 2017. MSR 2017 mining challenge dataset. Figshare archival copy posted 2022 |
| Java subset | https://github.com/monperrus/travistorrent-java-ci-build-dataset , 519,373 Java builds across 20 projects, convenient smaller slice |

**Note for the paper:** the age issue is a real reviewer risk. Add one sentence in `sec:travistorrent` acknowledging the 2017 cutoff and the platform's subsequent decline, and pair it with a modern cohort (item #3) if at all possible.

### 3.2 GHALogs and GitHub Actions workflow histories

See item #3 in the top five. Both listed there with URLs.

### 3.3 IDoFT: Illinois/International Dataset of Flaky Tests

| Field | Value |
|:--|:--|
| URL | https://github.com/TestingResearchIllinois/idoft , portal http://mir.cs.illinois.edu/flakytests |
| Contents | Continuously updated catalogue of confirmed flaky tests across many OSS projects, with flakiness category (order-dependent, non-order-dependent), project, module, test identifier, and fix status. Subsumes the original iDFlakies findings |
| iDFlakies framework | https://github.com/iDFlakies/iDFlakies , ICST 2019 paper https://ieeexplore.ieee.org/document/8730188 , dataset site https://sites.google.com/view/flakytestdataset |
| License | Open, CSV in-repo |

### 3.4 FlakeFlagger dataset

| Field | Value |
|:--|:--|
| URL | https://zenodo.org/records/4450723 , code https://github.com/AlshammariA/FlakeFlagger , paper https://www.jonbell.net/preprint/icse21-flakeflagger.pdf |
| Contents | `Project_Info.csv` (projects and revisions), build logs from 10,000 runs, surefire XML for failing tests, `test_results.csv`, `test_features.csv` with per-test behavioral features |
| Key features | Test execution time, overall test coverage, coverage of recently changed lines, third-party library usage |
| Finding to cite | Execution time and coverage of recently changed lines are effective flakiness predictors; source tokens and test smells are not |

**Relevance of 3.3 and 3.4 to PRESTO:** the paper's headline feature-importance result is that **testing infrastructure stability (20.3 percent importance) and test pass rate** are the strongest predictors. That is currently a claim about synthetic data with a domain-expert-specified correlation behind it, so it is close to circular. IDoFT and FlakeFlagger provide real evidence that test suite instability is measurable, varies substantially across projects, and predicts downstream outcomes. Citing them in Section `sec:feature_importance` converts "the copula said so" into "and this is consistent with real flakiness research". Cheap and worthwhile. Also relevant: "Practical Flaky Test Prediction using Common Code Evolution and Test History Data", https://arxiv.org/abs/2302.09330 .

### 3.5 Reproducible flaky-test failures dataset

| Field | Value |
|:--|:--|
| URL | https://arxiv.org/abs/2605.21677 |
| Contents | Reproducible flaky-test failures with complete failure logs, positioned as an improvement over DeFlaker and iDFlakies which lack full logs |

Recent; verify hosting and license on the arXiv record before citing.

### 3.6 Test coverage evolution

No single canonical dataset exists. Best available:

* **"A large-scale study of test coverage evolution"**, ASE 2018, https://dl.acm.org/doi/10.1145/3238147.3238183 . Cite for real coverage-over-time dynamics.
* **"Code Coverage and Postrelease Defects: A Large-Scale Study on Open Source Projects"**, https://www.researchgate.net/publication/319655487 . Directly relevant: real evidence on whether coverage predicts post-release defects. Useful counterweight to any over-strong claim about coverage as a performance predictor.
* **Codecov State of Open Source Code Coverage** reports, https://about.codecov.io/resource/2021-state-of-open-source-code-coverage/ . Industry benchmark distributions of coverage percentages across 60K+ OSS projects. Directly usable to check whether the generator's Beta-distributed coverage marginals are realistic.

***

## 4. Software performance and APM datasets linking changes or deployments to runtime outcomes

### 4.1 Mozilla Perfherder dataset

Item #1 in the top five. The only dataset in this category that links *code revisions* to *runtime performance* with expert-validated labels.

### 4.2 Live Mozilla Treeherder / Perfherder API

| Field | Value |
|:--|:--|
| URL | https://treeherder.mozilla.org/api/ , Perfherder docs https://wiki.mozilla.org/EngineeringProductivity/Projects/Perfherder , sheriffing process https://wiki.mozilla.org/TestEngineering/Performance/Sheriffing |
| Contents | Live, public, unauthenticated API for pushes, jobs, job durations, job results, performance signatures, performance datums, and alert summaries |
| Access | Public, rate-limited, no auth required for public repos (`mozilla-central`, `autoland`) |

**Relevance:** lets you extend item #1 beyond its May 2023 to May 2024 window, and lets you pull the *build and test job* side that the Zenodo artifact does not include. This is how you assemble a genuine multi-phase real dataset: Perfherder for the Performance Testing and Production-proxy phases, Treeherder jobs for Build and Test, Bugzilla for Requirements/Defects, `hg` or the GitHub mirror for Code.

### 4.3 Chromium performance dashboard (chromeperf) and Pinpoint

| Field | Value |
|:--|:--|
| URL | https://chromeperf.appspot.com/ , bisect docs https://chromium.googlesource.com/chromium/src/+/HEAD/docs/speed/bisects.md , dashboard code https://chromium.googlesource.com/catapult/+/HEAD/dashboard/README.md , measurement overview https://chromium.googlesource.com/chromium/src/+/main/docs/speed/how_does_chrome_measure_performance.md |
| Contents | Continuous benchmark timeseries across the chromium.perf waterfall, with regressions bisected down to individual changelists via Pinpoint |
| **Access caveat** | Perf data is **internal-only by default**; the dashboard requires a `@google.com` login for most series. Only a subset is public |

**Verdict:** conceptually the ideal dataset (continuous perf timeseries with culprit-CL attribution at massive scale) but **access-blocked**. Cite the infrastructure in related work as evidence that industry does exactly what PRESTO proposes. Do not plan a validation study around it.

### 4.4 Alibaba cluster trace, microservices v2022

| Field | Value |
|:--|:--|
| URL | https://github.com/alibaba/clusterdata/tree/master/cluster-trace-microservices-v2022 , program root https://github.com/alibaba/clusterdata |
| Contents | 13 days from Alibaba production clusters of 10,000+ bare-metal nodes. `MSRTMCR`: microservice call rate and **response time** for 28,000+ microservices across 470,000+ containers. `MSCallGraph`: 20M+ call graphs across 17,000+ microservices |
| Sampling | 0.5 percent trace sampling |
| Shuffled copy | Harvard Dataverse release (2024) with per-traceid file locality |
| License | Open, see repo terms |

**Relevance and limit.** This is real production response time at exactly the scale PRESTO's "ABC Cloud Provider, 200+ microservices" archetype imagines. **It has no SDLC side at all**: no commits, no builds, no releases, no test data. So it cannot validate the prediction task. Its correct uses are: (a) empirically ground the *marginal distributions* of the Production phase metrics in the generator, replacing assumed log-normals with fitted ones; (b) cite in Section `sec:external_validity` as evidence for what real microservice performance distributions look like, and specifically for heavy tails, which supports the paper's own transformation choices; (c) support the archetype's plausibility (200+ microservices is realistic).

### 4.5 RCAEval

| Field | Value |
|:--|:--|
| URL | https://github.com/phamquiluan/RCAEval , Zenodo https://zenodo.org/records/14590730 , Figshare https://figshare.com/articles/dataset/RCAEval_A_Benchmark_for_Root_Cause_Analysis_of_Microservice_Systems/31048672 , paper https://arxiv.org/abs/2412.17015 |
| Contents | 735 failure cases across Online Boutique, Sock Shop, Train Ticket. 11 fault types. RE1: 375 cases, metrics only, 49 to 212 metrics. RE2: 270 cases, 77 to 376 metrics, 8.6 to 26.9M logs, 39.6 to 76.7M traces. RE3: 90 cases, **code-level faults**, 68 to 322 metrics |
| Access | Open, pip-installable library |

**Relevance:** RE3 is the interesting one. Code-level fault injection with resulting telemetry is the closest public analogue to "a code change degraded runtime performance". It is testbed data rather than production data, but it is real measured telemetry from real running systems. Useful as (a) a Chaos Testing phase grounding, which is otherwise entirely unvalidated in the paper, and (b) a related-work citation showing that the SDLC-to-runtime link is actively studied.

### 4.6 Nezha

| Field | Value |
|:--|:--|
| URL | Paper https://dl.acm.org/doi/pdf/10.1145/3611643.3616249 (ESEC/FSE 2023) |
| Contents | Logs, metrics, traces from TrainTicket and OnlineBoutique with injected CPU contention, CPU consumption, network delay, and Java/Python code defects |

Similar profile to RCAEval, smaller. Worth a citation for the chaos/fault-injection phase.

### 4.7 LO2: Microservice API Anomaly Dataset of Logs and Metrics

| Field | Value |
|:--|:--|
| URL | https://arxiv.org/abs/2504.12067 , PROMISE 2025 https://dl.acm.org/doi/10.1145/3727582.3728682 |
| Contents | Paired logs and metrics for microservice API anomalies |

### 4.8 Loghub and Loghub-2.0

| Field | Value |
|:--|:--|
| URL | https://github.com/logpai/loghub , paper https://arxiv.org/abs/2008.06448 |
| Contents | 19 system log datasets. Six have ground-truth anomaly labels: HDFS-v1, HDFS-v3, Hadoop, OpenStack, BGL, Thunderbird. HDFS: 11.2M messages, 16,838 block sequences, 2.9 percent anomalous. BGL: 4.75M messages, 7.34 percent anomalous. Thunderbird: 200M+ messages, 0.49 percent anomalous |
| Analysis scripts | https://github.com/ait-aecid/anomaly-detection-log-datasets |

**Relevance:** Production phase incident-rate grounding. Real base rates of production anomalies (0.5 to 7 percent of events) are a sanity check on the generator's shock event probability of `p = 0.03` to `0.05`. That is a nice, specific, verifiable calibration claim you can make instead of an unsupported parameter choice. No SDLC side.

### 4.9 SPEC benchmarks

| Field | Value |
|:--|:--|
| URL | https://www.spec.org/ , SPEC Research Group https://research.spec.org/ |
| Relevance | **Low.** SPEC results are hardware and configuration benchmarks with no development process data. Cite only if you need a standard definition of a performance metric. Not a validation source |

### 4.10 Configuration-space performance prediction (already cited, for context)

The manuscript cites `ha2019` and `siegmund2015` as prior work reporting `R^2 > 0.95`. These operate on *configuration option* spaces, not process metrics, and the associated datasets (SPLConqueror and successors) are public. Worth one sentence making explicit that their high `R^2` comes from a deterministic configuration-to-performance mapping, which is a fundamentally easier problem than a stochastic process-to-outcome mapping. This reframes PRESTO's 0.387 as appropriate for its task rather than weak by comparison, and it is a defensible argument rather than special pleading.

***

## 5. Code complexity plus defect and incident outcome datasets

### 5.1 PROMISE / tera-PROMISE

| Field | Value |
|:--|:--|
| URL | http://promise.site.uottawa.ca/SERepository/ , tera-PROMISE at https://openscience.us/repo/ |
| Contents | The classic defect prediction corpora (CM1, JM1, KC1, PC1, ant, camel, jedit, log4j, lucene, poi, synapse, velocity, xalan, xerces and many more). Static code metrics paired with defect counts or binary defect labels, mostly at class or module level |
| Status | Both hosts have had intermittent availability over the years. Mirror what you use and archive it |

**Relevance:** the paper already names PROMISE in its exhaustive-search claim. Fine as-is. Not a viable validation source, since it has no temporal release structure and no runtime outcome. Its value is purely as a related-work anchor for "software metrics predict quality outcomes".

### 5.2 Unified Bug Dataset

| Field | Value |
|:--|:--|
| URL | http://www.inf.u-szeged.hu/~ferenc/papers/UnifiedBugDataSet/ |
| Contents | Aggregation of multiple public bug datasets into a common static-metric schema. Companion GitHub Bug Dataset at http://www.inf.u-szeged.hu/~ferenc/papers/GitHubBugDataSet/ |

### 5.3 ApacheJIT

| Field | Value |
|:--|:--|
| URL | https://zenodo.org/records/5907002 , paper https://arxiv.org/abs/2203.00101 , MSR 2022 https://dl.acm.org/doi/abs/10.1145/3524842.3527996 |
| Authors | Keshavarz, Nagappan |
| Contents | 106,674 commits from 14 Apache projects. 28,239 bug-inducing, 78,435 clean. Commit-level metrics as features, binary bug-inducing label. Includes a temporally separated test subset from the last 3 years, deliberately unbalanced to reflect deployment reality |

**Relevance:** methodologically the closest published analogue to what PRESTO does, and a good template. Note the design choice worth copying: a temporally held-out, deliberately unbalanced test set. PRESTO's 80/20 temporal split is fine but ApacheJIT's framing is more rigorous and is a citable precedent for the validation protocol.

### 5.4 Defectors

| Field | Value |
|:--|:--|
| URL | https://doi.org/10.5281/zenodo.7708984 |
| Contents | Large, diverse Python dataset for defect prediction |

### 5.5 Mozilla regressors-regressions dataset

| Field | Value |
|:--|:--|
| URL | https://github.com/mozilla/regressors-regressions-dataset |
| Contents | Bug-introducing and bug-fixing commit sets derived from Mozilla Bugzilla, maintained by Mozilla itself |

**Relevance:** another join partner for the Mozilla validation route (item #1). Gives a defect-outcome label alongside the performance-outcome label.

### 5.6 Bug Prediction Dataset (D'Ambros et al.)

| Field | Value |
|:--|:--|
| URL | http://bug.inf.usi.ch/ |
| Contents | Metrics and models from several Eclipse-family projects with change and defect history |

### 5.7 Defects4J, CoREBench, SIR, RegMiner

| Name | URL | Note |
|:--|:--|:--|
| Defects4J | https://github.com/rjust/defects4j | 395+ reproducible real bugs, Java. Test-execution research, not metrics prediction |
| CoREBench | http://www.comp.nus.edu.sg/~release/corebench/ | Systematically extracted regression errors |
| SIR | http://sir.unl.edu/portal/index.php | Software-artifact Infrastructure Repository, artifacts with test suites and seeded faults |
| RegMiner | https://arxiv.org/abs/2109.12389 , https://dl.acm.org/doi/10.1145/3540250.3558929 | 1,035 replicable regressions across 147 projects, automated mining |

***

## 6. DORA and DevOps benchmark statistics for validating synthetic parameters

### 6.1 DORA / Accelerate State of DevOps

Item #4 in the top five. Primary and only authoritative source for the four key metrics. All years at https://dora.dev/research/ .

**Reproduced 2024 figures for the calibration check** (also saved as CSV under `samples/`):

| Tier | Share of respondents | Deployment frequency | Lead time for change | Change failure rate | Failed deployment recovery time |
|:--|:--|:--|:--|:--|:--|
| Elite | 19 percent | On demand | Under one day | About 5 percent | Under one hour |
| High | 22 percent | Once per day to once per week | (see report) | (see report) | (see report) |
| Medium | 35 percent | Once per week to once per month | (see report) | Lower than High in 2024 | (see report) |
| Low | 25 percent | Less than once per month | (see report) | (see report) | (see report) |

Headline ratios frequently cited: Elite deploy 182x more frequently than Low, 127x faster lead times, 8x lower change failure rate.

**Warning on secondary sources.** Many vendor blogs restate DORA tier boundaries with numbers that do not appear in the report. Cite `dora.dev` or the Google Research listing directly, never a vendor blog, for any number that goes into the manuscript. The values above should each be confirmed against the PDF before they appear in print.

### 6.2 CNCF DevStats

| Field | Value |
|:--|:--|
| URL | https://k8s.devstats.cncf.io/ , code https://github.com/cncf/devstats , metric definitions https://github.com/cncf/devstats/blob/master/METRICS.md , dashboards https://github.com/cncf/devstats/blob/master/DASHBOARDS.md |
| Contents | Continuously updated developer-activity metrics for ~80 Kubernetes repos and all CNCF projects. Postgres + InfluxDB + Grafana. Sourced from GH Archive and the GitHub API, refreshed hourly |
| Access | Public Grafana, open-source toolchain, self-hostable |

**Relevance:** real, current, per-project time series of PR throughput, review latency, issue resolution time, contributor counts and commit velocity. These are genuine Requirements/Code/Process phase metrics at weekly granularity for large real projects. Combined with each project's public release tags you get real deployment frequency and lead time for real large-scale systems, which is an independent empirical check on the DORA survey numbers *and* on the generator's cadence assumptions. This is an underused resource and would look sophisticated in a paper.

### 6.3 Wikimedia public engineering data

| Field | Value |
|:--|:--|
| Incident reports | https://wikitech.wikimedia.org/wiki/Incident_status , archive at Category:Incident documentation, template at https://wikitech.wikimedia.org/wiki/Incident_response/Full_report_template , scorecard at https://wikitech.wikimedia.org/wiki/Incident_Scorecard |
| Deployment log | Server Admin Log (SAL), linked from every incident report |
| Code review | https://gerrit.wikimedia.org/ |
| Issue tracking | https://phabricator.wikimedia.org/ |
| Production metrics | https://grafana.wikimedia.org/ (public) |
| Access | All public, no authentication |

**Why this is worth serious consideration.** Wikimedia is, as far as this survey found, **the only large-scale production system where all eight of PRESTO's phases are simultaneously public**: requirements and issues in Phabricator, code and review in Gerrit, build and test in the public CI, deployment in the SAL and the weekly train schedule, production latency and availability in public Grafana, and structured incident postmortems with duration and impact on Wikitech. There is no single packaged dataset; it would require construction. But it is the only realistic path to a *genuine* end-to-end SDLC-to-production-uptime validation using public data.

**Honest assessment of cost:** building this is a multi-week data engineering effort, not a revision-cycle task. It is the right answer for a follow-up paper or a major-revision commitment. For the current submission, mention it explicitly in Future Work as a concrete, named plan rather than the vague "real-world validation with production SDLC data remains essential future work" currently in Section `sec:synthetic_data`. Naming a specific feasible plan reads far better to reviewers than a generic promise.

### 6.4 Incident and outage aggregators

| Source | URL | Note |
|:--|:--|:--|
| VOID | https://www.thevoid.community/database | See item #5. Best of these |
| danluu/post-mortems | https://github.com/danluu/post-mortems | Curated list of public postmortems, categorized by root cause. Includes pointers to Wikimedia postmortems, Lorin Hochstein's incident list, and Nat Welch's parsed-postmortem database |
| GCP Cloud Status Dashboard dataset | https://github.com/salrashid123/gcp_cloud_status_dataset | Google Cloud Service Health events in BigQuery, queryable |
| CloudDowntime | https://www.clouddowntime.com/ | Documented methodology and open dataset of major customer-impacting AWS/Azure/GCP outages |
| IncidentHub reliability reports | https://blog.incidenthub.cloud/ | Monitors 1,125+ providers via public status pages, APIs, webhooks, RSS. Periodic aggregate reports |
| StatusGator | https://statusgator.com/services/public-cloud | Commercial aggregator, limited free access |

**Relevance:** these give real empirical distributions of outage frequency and duration for production systems. Use for Production phase calibration and for the construct-validity argument in item #5. Note that most are commercial or semi-curated, so treat aggregate statistics as indicative rather than as a research-grade dataset, and say so if you cite them.

### 6.5 Empirical studies with citable incident statistics

These are papers, not datasets, but they carry numbers that directly support or challenge the paper's framing:

* **Microsoft Teams high-severity incidents:** 13 percent caused by software rollouts to production. Google-reported figure: about 16 percent of failures deployment-related. See "How to fight production incidents? An empirical study on a large-scale cloud service", https://www.researchgate.net/publication/365200239 . **This is a double-edged citation and you should engage with it rather than avoid it.** If only 13 to 16 percent of production incidents are deployment-caused, then the theoretical ceiling on predicting production uptime from release-time SDLC metrics is bounded well below 1. That is a *good* argument for PRESTO: it reframes `R^2 = 0.387` as recovering a substantial fraction of the explainable variance rather than falling short of an unattainable 1.0. Putting this in Section `sec:model_perf` or the Discussion turns the paper's weakest number into a defensible one.
* **Netflix and Hulu incident prediction:** 2,261 incidents, hybrid model using only historical data. https://www.sciencedirect.com/science/article/abs/pii/S0268401218309381
* **LLM service outages, ICPE 2025:** https://atlarge-research.com/pdfs/2025-icpe-llm-service-analysis.pdf
* **GenAI cloud service production incidents:** https://arxiv.org/abs/2504.08865

### 6.6 Mozilla release health as a real uptime-analogue

| Field | Value |
|:--|:--|
| Crash Stats (Socorro) | https://crash-stats.mozilla.org/ , public data only |
| Mission Control | https://missioncontrol.telemetry.mozilla.org/ , crash rates by release and platform |
| Telemetry docs | https://docs.telemetry.mozilla.org/ |

**Relevance:** crash rate per release is a real, public, release-level *reliability* outcome. It is not uptime, but for a client application it is the structural equivalent: a per-release stability percentage. Combined with item #1 and item #4.2 this gives Mozilla two independent real outcome variables (performance regression alerts, crash rate) against a common set of real SDLC features. That is a credible real-world analogue of the paper's core prediction task, at release granularity, using entirely public data. **If you only do one new thing, do this plus item #1.**

***

## 7. Summary recommendations

Ordered by effort-to-value.

**Low effort, do before submission regardless of anything else:**

1. **Fix the exhaustive-search claim.** Sections `sec:synthetic_data` and `sec:external_validity` both assert no such public dataset exists. The Mozilla ICPE 2025 artifact (item #1) falsifies it as stated. Narrow the claim to release-level multi-phase SDLC metrics paired with production availability, and cite the Mozilla dataset explicitly as the closest existing work. Turning a discoverable error into a demonstrated awareness of the literature is a net gain.
2. **Fix or explain the DORA cadence arithmetic.** 170 releases in 5 years is not DORA "High"; 150 in 4 years is not DORA "Elite". Either decouple "release" from "deployment" in the prose or regenerate. See item #4.
3. **Add SmartSHARK and SQuaD to related work.** The multi-source SDLC integration contribution is currently stated without acknowledging prior art. Reposition rather than defend.
4. **Add the 13 to 16 percent deployment-caused-incident statistic** to reframe the `R^2` ceiling. See item 6.5.
5. **Cite VOID on skewed incident duration** in construct validity, and IDoFT/FlakeFlagger in feature importance.
6. **Add one sentence** to `sec:travistorrent` acknowledging the 2017 data cutoff.

**Medium effort, strongly recommended for a major revision:**

7. **Build the Mozilla validation** (items #1 + #4.2 + #6.6). Real runtime performance target, real build and test features, public and CC-BY. This is the single change that would move External Validity off "Unmitigated".
8. **Add a GHALogs cohort** alongside TravisTorrent for a modern, two-platform CI replication (item #3).
9. **Recalibrate generator marginals** against SQuaD (code metrics), Alibaba v2022 (production response time), Loghub (anomaly base rates), and Codecov (coverage distributions). Replaces asserted calibration with demonstrated calibration.

**High effort, name it as Future Work rather than attempting it now:**

10. **Construct the Wikimedia end-to-end dataset** (item #6.3). The only realistic public path to all eight phases plus real production availability. Multi-week effort. Naming it concretely is worth more than a vague promise.

***

## 8. Confidence and coverage disclosure

**Coverage confidence: moderate to good, roughly 75 percent** of likely-relevant publicly available resources for this specific intersection. Well covered: MSR data showcase artifacts, CI/CD datasets, flaky test datasets, microservice telemetry benchmarks, DORA. Less well covered: non-English datasets (the Chinese AIOps Challenge series 2020 to 2022 and the CloudWise GAIA dataset were surfaced only indirectly and were not verified); industry consortium data behind membership walls; anything published after roughly mid-2026.

**Verification status.** Every URL in this catalog came from a search result or a direct page fetch during this session. However, only the following were fetched and read directly: the Mozilla Zenodo record, the GHALogs GitHub README, awesome-msr, and the Directory of MSR Datasets. **All other dataset sizes, field lists and licenses are reported from search-result summaries and have not been independently confirmed.** Treat them as leads, not facts. Before any of these numbers enter the manuscript, open the record and check.

**Specific items needing human spot-check before citation:**

* GHALogs license is unstated in the GitHub README. Check the Zenodo record.
* SQuaD is very recent (November 2025 arXiv, MSR 2026 submission) and may not be peer-reviewed yet. Check status before relying on it as a validated source.
* The DORA 2024 tier boundary table above is assembled partly from secondary reporting. Several cells are marked "(see report)" precisely because reliable values were not obtained. **Confirm every cell against the official PDF.** Vendor blogs restating DORA numbers are frequently wrong.
* "A Dataset of Reproducible Flaky-Test Failures" (arXiv 2605.21677) is very recent; hosting and license unverified.
* Alibaba clusterdata licensing terms were not read directly.
* The claim that Wikimedia has all eight phases publicly available is my inference from the components found, not something I verified end to end. The critical unknown is whether Wikimedia CI job-level results are retained and queryable far enough back to build a release-level time series. **Verify this before committing to it in Future Work.**

**Where this catalog may be wrong:**

* *The Wikimedia recommendation is the least validated and the most consequential.* It is presented as the ideal path but rests on the least verification. If CI history retention is short, the plan collapses.
* *The DORA cadence criticism assumes "release" means "deployment".* If the authors intend a release train abstraction, the criticism is softer than stated, though the prose would still need clarifying since a reviewer will make the same assumption I did.
* *I did not find any dataset that fully solves the paper's problem.* The honest conclusion of this search is that the paper's core gap claim is *substantially* correct even though its specific wording is falsifiable. No public dataset pairs multi-phase release-level SDLC process metrics with production availability. Mozilla comes closest and covers maybe half the phases with a performance rather than availability target. If a reviewer demands full real-world validation, the correct response is that the data does not exist publicly, not that it was overlooked.
* *Hugging Face Hub returned no relevant results* across three query formulations for SDLC, CI, build, and DevOps datasets. Either the Hub genuinely lacks this category (plausible, since it skews toward NLP and code-generation corpora) or my queries were poorly matched. Low confidence in this negative result; a manual browse of the Hub's `software-engineering` tag would be worth ten minutes.
* *Contested:* whether adding a second real-world validation actually helps. If the Mozilla study also produces near-zero `R^2`, the paper is arguably worse off than with one weak validation. The counterargument, which I find more persuasive, is that a well-executed negative result on real data plus a clear explanation is stronger than an unmitigated Critical validity threat. But this is a judgment call the authors should make deliberately rather than by default.
