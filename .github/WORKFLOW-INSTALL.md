# Optional: enable weekly snapshot workflow

A prebuilt GitHub Actions workflow that re-snapshots every Sunday lives
at `scripts/weekly-snapshot.yml`. It was kept out of `.github/workflows/`
on the initial push because the publishing token lacked the `workflow`
OAuth scope.

To enable:

```bash
mkdir -p .github/workflows
cp scripts/weekly-snapshot.yml .github/workflows/weekly-snapshot.yml
git add .github/workflows/weekly-snapshot.yml
git commit -m 'ci: enable weekly snapshot workflow'
git push
```

GitHub web UI also works: paste the file into the Actions tab as a new workflow.
