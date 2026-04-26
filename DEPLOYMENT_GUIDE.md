# Deployment Guide: Flight Pipeline with CI/CD and Dashboard

This guide covers setting up the complete flight pipeline with GitHub Actions CI/CD and a dashboard for monitoring pipeline runs.

## What's New

### 1. GitHub Actions CI Pipeline (.github/workflows/ci.yml)
- **Lint Job**: Checks code quality with `ruff`
- **Test Job**: Runs the test suite with `pytest`
- **Sample Ingest Job**: Validates pipeline logic with a dry-run ingest
- **Triggers**: 
  - On push to main/develop branches
  - On pull requests
  - Daily schedule (2 AM UTC)

### 2. Dashboard Generator (utils/generate_dashboard.py)
- Queries `pipeline_runs` table for recent runs
- Generates an HTML dashboard with:
  - Summary statistics (success rate, total records processed)
  - Trend chart (last 10 runs)
  - Run history table with detailed metrics
  - Responsive design with modern UI
- Automatically generated after each non-dry-run ingest
- Saved as `dashboard.html` in the project root

### 3. Development Dependencies
Added to `pyproject.toml`:
- `pytest>=7.4.0` - Testing framework
- `ruff>=0.1.0` - Fast Python linter

## Setup Instructions

### Step 1: Prepare Your Repository

Before pushing to GitHub, set up your local repository:

```bash
cd flight_pipeline

# Initialize git if not already done
git init

# Create .github/workflows directory
python setup_cicd.py

# Or manually:
mkdir -p .github/workflows
cp ci.yml .github/workflows/ci.yml
```

### Step 2: Install Development Dependencies

```bash
# Install dev dependencies locally
pip install -e ".[dev]"
```

### Step 3: Test Locally (Optional)

Before pushing, verify the CI pipeline will succeed:

```bash
# Run tests
pytest tests/ -v

# Run linter
ruff check flight_pipeline/

# Run sample dry-run ingest (validates logic)
python pipelines/run_ingestion.py --source all --dry-run
```

### Step 4: Configure .gitignore

Ensure sensitive files are not committed:

```bash
# Already configured in .gitignore:
.env           # Secrets/database credentials
.env.*         # Any environment file variants
__pycache__/   # Python cache
.pytest_cache/ # Test cache
venv/          # Virtual environment
declaflights/  # Virtual environment
```

**IMPORTANT**: Never commit `.env` or database connection strings to version control.

### Step 5: Push to GitHub

```bash
# Add all files except those in .gitignore
git add -A

# Commit with appropriate message
git commit -m "Add CI pipeline and dashboard infrastructure

- GitHub Actions workflow for lint, test, sample ingest
- Dashboard generator for pipeline run metrics
- Development dependencies (pytest, ruff)
- Integrated dashboard generation into pipeline

Co-authored-by: Copilot <223556219+Copilot@users.noreply.github.com>"

# Push to your repository
git remote add origin https://github.com/Riekobrian/worldaerodata.git
git branch -M main
git push -u origin main
```

## Using the Dashboard

### Automatic Generation
The dashboard is automatically generated after each successful pipeline run (non-dry-run):

```bash
python pipelines/run_ingestion.py --source all
# → dashboard.html is generated at the end
```

### Manual Generation
To generate the dashboard manually:

```bash
python -c "
from utils.generate_dashboard import fetch_pipeline_runs, generate_html_dashboard
from pathlib import Path

runs = fetch_pipeline_runs(limit=20)
html = generate_html_dashboard(runs)
Path('dashboard.html').write_text(html)
print('Dashboard generated: dashboard.html')
"
```

### Viewing the Dashboard
1. Open `dashboard.html` in a web browser
2. View:
   - Summary statistics (total runs, success rate)
   - Trend chart of record processing
   - Detailed run history table

## GitHub Actions Workflow

### Viewing Workflow Runs
1. Go to your repository on GitHub
2. Click on "Actions" tab
3. See the list of CI runs
4. Click on a run to see details

### Workflow Jobs

#### Lint & Format Check
- Installs dependencies with `pip install -e ".[dev]"`
- Runs `ruff check flight_pipeline/`
- Non-blocking (continues even if it fails)

#### Run Tests
- Installs dev dependencies
- Runs `pytest flight_pipeline/tests/ -v`
- Blocks if tests fail

#### Sample Dry-Run Ingest
- Runs pipeline in dry-run mode with dummy database credentials
- Validates that all connectors, mappers, and validators work
- Non-blocking (continues even if it fails)

## Troubleshooting

### Tests Failing in CI
1. Check the GitHub Actions log
2. Run tests locally: `pytest tests/ -v`
3. Fix issues and commit
4. Push again to re-run CI

### Dashboard Not Generating
- Dashboard only generates after non-dry-run ingests
- Requires `FLIGHT_PIPELINE_DB_DSN` to be set
- Check logs: `python pipelines/run_ingestion.py --source all --log-level DEBUG`

### Secrets in Commit
If you accidentally committed `.env`:
1. **Never push the commit**
2. Remove the file: `git rm .env --cached`
3. Commit: `git commit -m "Remove .env file"`
4. Rotate any exposed secrets

## Performance Notes

- **Lint Check**: ~30 seconds
- **Test Suite**: ~60 seconds
- **Sample Ingest**: ~30-120 seconds depending on data sources
- **Total CI Runtime**: ~3-5 minutes per run

## Files Added/Modified

### New Files
- `.github/workflows/ci.yml` - GitHub Actions workflow
- `utils/generate_dashboard.py` - Dashboard generator script
- `setup_cicd.py` - Setup helper script

### Modified Files
- `pyproject.toml` - Added dev dependencies
- `pipelines/run_ingestion.py` - Integrated dashboard generation

## Next Steps

1. ✓ Commit and push to GitHub
2. Watch GitHub Actions tab for first CI run
3. Check dashboard.html for run metrics
4. Configure production database (if applicable)
5. Set up database backups
6. Monitor CI runs for failures

## Environment Variables Required

### For Local Development
```bash
FLIGHT_PIPELINE_DB_DSN=postgresql://user:password@localhost:5432/declaflights
```

### For CI (dry-run)
Set automatically to a dummy value. No secrets needed!

### For Production
Set `FLIGHT_PIPELINE_DB_DSN` as a GitHub secret:
1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `FLIGHT_PIPELINE_DB_DSN`
4. Value: Your production database DSN
5. (Optional) Update CI workflow to use the secret

## Questions?

See the main README.md for general project documentation.
