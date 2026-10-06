# Getting this repository a DOI on Zenodo

This repository is small (~88MB total, no file over 20MB) and needs no packaging step — it's
pushed to GitHub as-is, then archived automatically by Zenodo's GitHub integration when you tag a
release. That's the standard, citable-software-repository flow, and it sidesteps GitHub's 100MB
per-file hard limit entirely since nothing here comes close.

## 1. Push to GitHub

```bash
cd /Volumes/4TB/research-data-and-code/zenado/presto-data
git init -b main
git add -A
git commit -m "Initial commit: PRESTO research compendium"
git remote add origin https://github.com/<your-username>/presto-data.git
git push -u origin main
```

(If a `presto-data` repo doesn't exist yet on GitHub, create it first — public, no README/license
auto-init since this repo already has its own.)

## 2. Enable Zenodo's GitHub integration

1. Log in at https://zenodo.org with your GitHub account (or link GitHub under
   **Account → Linked accounts** if you're already logged in another way).
2. Go to https://zenodo.org/account/settings/github/.
3. Find `<your-username>/presto-data` in the repository list and flip the toggle **on**. This must
   be done *before* you create the release you want archived — Zenodo only picks up releases
   created after the toggle is enabled.

## 3. Create a GitHub release

```bash
git tag -a v1.0.0 -m "PRESTO research compendium v1.0.0"
git push origin v1.0.0
gh release create v1.0.0 --title "v1.0.0" --notes "Initial Zenodo-archived release of the PRESTO research compendium."
```

Or via the GitHub web UI: **Releases → Draft a new release**, pick the `v1.0.0` tag, publish.

Zenodo detects the new release within a few minutes, downloads a snapshot of the repository at
that tag, and mints a DOI automatically. You'll see it appear on your Zenodo GitHub settings page
and get an email notification.

## 4. Finish the metadata on Zenodo

Zenodo pre-fills the deposit from `.zenodo.json` in the repo root (already present here) — title,
authors + ORCID, description, keywords, license, and the `related_identifiers` pointing at the
four source datasets this compendium derives from. Open the new deposit on Zenodo and check:

- **Related/alternate identifiers** rendered correctly from `.zenodo.json`.
- **License**: CC-BY-4.0 for data/paper; note in the description (already done) that `code/` is
  separately MIT-licensed.
- Once the paper itself has a DOI (preprint or published), add a new related identifier with
  relation **isSupplementTo** or **isPartOf**, and push an update — Zenodo versions releases, so
  this doesn't require a new DOI, just a new version of the existing record (create a new GitHub
  release `v1.0.1` etc.).

## 5. Releasing a new version (e.g. v2.0.0 for the v6 manuscript)

The Zenodo integration is already enabled for this repo, so each new GitHub release becomes a new
**version** of the same Zenodo record: a new version DOI, under the unchanged concept DOI
`10.5281/zenodo.22005438`.

```bash
cd /Volumes/4TB/research-data-and-code/zenado/presto-data
git switch main && git merge --no-ff v6-revision
git push origin main
git tag -a v2.0.0 -m "PRESTO research compendium v2.0.0 (matches v6 manuscript)"
git push origin v2.0.0
gh release create v2.0.0 --title "v2.0.0" --notes "Matches the round-3 (v6) revision of the MDPI Technologies manuscript."
```

Then: wait for the new version on Zenodo, note its version DOI, and put either that version DOI
or the concept DOI (`10.5281/zenodo.22005438`, always resolves to the latest) into the
manuscript's Data Availability Statement and Reproducibility paragraph, `CITATION.cff` (`doi:`),
and `README.md`.

Version history so far: v1.0.0 / v1.0.1 = initial August 2026 snapshot (v3 manuscript), DOI
`10.5281/zenodo.22005439`.

## What this DOI does and doesn't include

This deposit is the **code + paper + small derived data** compendium. It does **not** re-host the
bulk raw real-world datasets (TravisTorrent, Mozilla Perfherder, GHALogs — several GB each) —
those stay at their own original DOIs, linked via `related_identifiers` and documented per-source
in `real-data/<source>/DOWNLOAD.md`. This is the standard pattern for reproducibility packages:
GitHub/Zenodo hosts the small, versioned, citable code+paper; large third-party data stays at its
authoritative source rather than being duplicated. Cite all four `related_identifiers` DOIs
alongside this one if you reuse the real-world validation results.

If you'd rather have Zenodo also host full copies of the large datasets directly (bypassing
GitHub's size constraints via Zenodo's own web uploader, which accepts files up to 50GB), that's a
separate, second Zenodo deposit — build it by re-running the fetch steps in each `DOWNLOAD.md`
locally, zipping the results, and uploading through https://zenodo.org/deposit/new directly rather
than through the GitHub integration. Link it back to this deposit via a `related_identifiers`
entry (`isSupplementedBy`) if you do this.
