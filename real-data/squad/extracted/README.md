This is a **re-direction** Zenodo repository that presents the _"SQuaD: The Software Quality Dataset"_ submitted to MSR 2026 Data and Tool Showcase Track, and provides **the link address to each of the supplementary materials (see below).**

**Version:** 1.0 \
**DOI:** [https://doi.org/10.5281/zenodo.17566690](https://doi.org/10.5281/zenodo.17566690) \
**Authors:** Mikel Robredo, Matteo Esposito, Davide Taibi, Rafael Peñaloza, Valentina Lenarduzzi 
**Affiliations:** University of Oulu, University of Southern Denmark, University of Milano-Bicocca 

---

## Access and Usage

The dataset and all supplementary materials are available through Zenodo and IDA* repositories:

- **CSV Raw Data (IDA):** [https://doi.org/10.23729/fd-c528d131-2c8c-3e61-91f1-a075931e73dc](https://doi.org/10.23729/fd-c528d131-2c8c-3e61-91f1-a075931e73dc) 
- **MongoDB BSON (IDA):** [https://doi.org/10.23729/fd-f9dc7d2c-0465-3991-961f-56128ee518d0](https://doi.org/10.23729/fd-f9dc7d2c-0465-3991-961f-56128ee518d0) 
- **Replication Package (Zenodo):** [https://doi.org/10.5281/zenodo.17541471](https://doi.org/10.5281/zenodo.17541471)

On **IDA:**  IDA ([ida.fairdata.fi](https://ida.fairdata.fi/)) is a research data storage service organized by the Finnish Ministry of Education and Culture and produced by  [CSC — IT Center for Science](http://www.csc.fi/). The service is intended for storing stable research data, both raw data and processed data, which is included to research datasets published in the FAIRdata (FAIR: _Findable, Accessible, Interoperable, and Reusable_) Etsin service. The service is offered free of charge to users affiliated with Finnish universities and polytechnics and Finnish research institutes.

Each link corresponds to a specific data access format, along with replication scripts and diagrams for database structure.

- Main abbreviations:
  - **Static Analysis Tool (SAT):** A software static analysis tool is an automated program that examines a software's source code without executing it to find potential bugs, security vulnerabilities, and deviations from coding standards.
  - **Issue Tracking System (ITS):** A software issue tracking system is a tool used to manage and track software bugs, feature requests, and other problems from initial report to final resolution. It acts as a centralized database, allowing teams to create, assign, and monitor issues, ensuring a structured and organized approach to problem-solving and collaboration. 

---

## Overview

The **Software Quality Dataset (SQuaD)** is a **multi-dimensional, time-aware collection of software quality metrics** extracted from 450 mature open-source projects across diverse ecosystems, including **Apache**, **Mozilla**, **FFmpeg**, and the **Linux kernel**.

SQuaD integrates **nine state-of-the-art Static Analysis Tools (SATs)** and combines both **product** and **process** metrics to support large-scale empirical research on software quality, maintainability, evolution, and technical debt.

This dataset was submitted to a major software engineering conference in 2025 and is the result of a seven-month large-scale mining effort.

---

## Dataset Summary

| Attribute | Description |
|------------|-------------|
| **Projects analyzed** | 450 open-source projects |
| **Releases analyzed** | 63,586 releases/tags |
| **Static Analysis Tools** | 9 tools (SonarQube, CodeScene, PMD, Understand, CK, JaSoMe, RefactoringMiner, RefactoringMiner++, PyRef) |
| **Unique metrics** | 725 metrics |
| **Defect tickets** | 628,178 |
| **Commits analyzed** | 2,622,413 |
| **Detected vulnerabilities** | 1,479 CVEs and 175 CWEs |
| **Average project age** | 9 years |
| **Average LOC per project** | 125,500 |
| **Average GitHub stars** | 2,465 |
| **Average contributors** | 104 |

---

## Data Contents

The dataset includes a variety of entities and metric tables, covering product, process, and vulnerability information. 
Each entity corresponds to a CSV table or a MongoDB collection:

| Table | Description |
|--------|--------------|
| **PROJECTS** | GitHub repository metadata |
| **COMMITS** | Commit hash, message, date, author alias |
| **ISSUES** | Issue tickets from GitHub, Jira, and Bugzilla |
| **RELEASES** | Identifiers of project releases and related commit hashes |
| **GITHUB_METRICS** | Stars, contributors, watchers, and project statistics |
| **PRJ_ITS_VLN_LINKAGE** | Links between projects, issue trackers, and detected vulnerabilities |
| **CVE / CWE** | Official vulnerability and weakness data from NIST and MITRE |
| **PROCESS_METRICS** | 14 process metrics computed for each release |
| **TOOL tables** | Output metrics from each SAT at method, class, file, and project levels |

---

## Available Formats

SQuaD is distributed in **two complementary formats** to facilitate different research and analysis needs:

### 1. CSV Format
- Each entity is provided as a separate CSV file.
- Ideal for direct exploration, statistical analysis, and integration into scripts or notebooks.
- Mirrors the same relational structure as the MongoDB database.

### 2. MongoDB Format
- A **NoSQL** version of the dataset is provided as a **compressed BSON dump** (Zstandard-compressed).
- Can be imported into MongoDB for scalable querying and time-aware analyses.
- Recommended for researchers dealing with large-scale data analytics or custom pipelines.

**NOTE:** - The full data weighs approximately **1.9 TB**, so ensure sufficient **storage** and **RAM** before extraction and import.   

#### Step 1 — Decompress the Archive (Zstandard)

The dataset is distributed as a `.tar.zst` file. To extract it, install **Zstandard** and decompress as follows:

```bash
# Install Zstandard (if not already installed)
sudo apt install zstd

# Decompress the archive (this may take several hours)
unzstd SQuaD_MongoDB_Dump.tar.zst

# Extract the BSON dump files
tar -xvf SQuaD_MongoDB_Dump.tar
```

#### Step 2 — Import into MongoDB
- Once decompressed, you can import each collection using mongorestore (bundled with MongoDB tools):
```bash
# Example: restore entire database
mongorestore --db squad_db /path/to/SQuaD_MongoDB_Dump
```

---

## Methodology Overview

The **dataset construction** follows four key stages (illustrated in the paper’s Figure 1):

1. **Mining version control data**
   - Cloned 501 repositories (filtered to 450 active, mature projects).
   - Retrieved commits, tags, issues, and metadata from issue tracking systems (ITS) such as GitHub, Jira, and Bugzilla.

2. **Mining software quality metrics** 
   - Applied nine SATs in parallel across all releases. 
   - Extracted metrics at multiple granularity levels (method, class, file, project).

3. **Extracting vulnerabilities** 
   - Parsed CVE and CWE references from issue tickets. 
   - Fetched official vulnerability descriptions via NIST and MITRE APIs.

4. **Collecting process metrics** 
   - Computed 14 release-level process metrics (e.g., churn, contributor count, commit density) using GitPython.

---

## Research Opportunities

SQuaD provides a comprehensive foundation for a variety of software engineering research domains:

- **Software evolution and maintainability analysis**
- **Defect prediction and Just-In-Time learning**
- **Technical debt and code smell benchmarking**
- **Refactoring impact analysis**
- **Software vulnerability detection and risk assessment**
- **Transformer-based and AI-driven quality modeling**

Its combination of product and process metrics supports both statistical and machine learning–based investigations.

## Acknowledgments

This work was supported by:
- **CSC – IT Center for Science, Finland** (Mahti Supercomputer, Allas Cloud Storage, cPouta services)
- **FAST Doctoral Research Network**, funded by the Finnish Ministry of Education and Culture 
- **SciTools**, for providing academic support and licenses for *Understand*