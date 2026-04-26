#!/usr/bin/env python3
"""
Setup script to prepare GitHub Actions workflow and integrate dashboard generation.
Run this once to set up the CI/CD pipeline infrastructure.
"""

import shutil
from pathlib import Path


def setup_github_workflows():
    """Set up .github/workflows directory with CI configuration."""
    
    repo_root = Path(__file__).parent
    workflows_dir = repo_root / '.github' / 'workflows'
    
    # Create directory structure
    workflows_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created directory: {workflows_dir}")
    
    # CI workflow configuration
    ci_yml_content = """name: CI Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC

jobs:
  lint:
    runs-on: ubuntu-latest
    name: Lint & Format Check
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      
      - name: Lint with ruff
        run: ruff check flight_pipeline/
        continue-on-error: true

  test:
    runs-on: ubuntu-latest
    name: Run Tests
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ".[dev]"
      
      - name: Run pytest
        run: pytest flight_pipeline/tests/ -v --tb=short

  sample-ingest:
    runs-on: ubuntu-latest
    name: Sample Dry-Run Ingest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e .
      
      - name: Run sample dry-run ingest (validates logic)
        run: |
          cd flight_pipeline
          python pipelines/run_ingestion.py --source all --dry-run --log-level INFO
        continue-on-error: true
        env:
          # Dummy DB string for dry-run (not actually used)
          FLIGHT_PIPELINE_DB_DSN: postgresql://dummy:dummy@localhost:5432/dummy
"""
    
    ci_yml_path = workflows_dir / 'ci.yml'
    ci_yml_path.write_text(ci_yml_content)
    print(f"✓ Created workflow: {ci_yml_path}")


def integrate_dashboard_generation():
    """Integrate dashboard generation into the pipeline."""
    
    repo_root = Path(__file__).parent
    run_ingestion_script = repo_root / 'pipelines' / 'run_ingestion.py'
    
    if not run_ingestion_script.exists():
        print(f"✗ Could not find {run_ingestion_script}")
        return False
    
    content = run_ingestion_script.read_text()
    
    # Check if dashboard generation is already integrated
    if 'generate_dashboard' in content:
        print("✓ Dashboard generation already integrated")
        return True
    
    # Add import at the top
    import_line = "from utils.generate_dashboard import generate_html_dashboard"
    if import_line not in content:
        # Find the imports section and add our import
        lines = content.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('from ') or line.startswith('import '):
                insert_idx = i + 1
            else:
                break
        
        lines.insert(insert_idx, import_line)
        content = '\n'.join(lines)
    
    # Add dashboard generation at the end of main() or at the end of script
    dashboard_call = """
    # Generate dashboard if database is available
    try:
        from utils.generate_dashboard import fetch_pipeline_runs, generate_html_dashboard
        runs = fetch_pipeline_runs(limit=20)
        if runs:
            html = generate_html_dashboard(runs)
            dashboard_path = Path("dashboard.html")
            dashboard_path.write_text(html)
            logger.info(f"Dashboard generated: {dashboard_path}")
    except Exception as e:
        logger.debug(f"Dashboard generation skipped: {e}")
"""
    
    # Append to file if not already present
    if 'Dashboard generated' not in content:
        content = content + '\n' + dashboard_call
        run_ingestion_script.write_text(content)
        print(f"✓ Integrated dashboard generation into {run_ingestion_script}")
        return True
    
    print("✓ Dashboard generation already integrated")
    return True


def main():
    """Run setup."""
    print("Setting up CI/CD pipeline infrastructure...\n")
    
    try:
        setup_github_workflows()
        print()
        integrate_dashboard_generation()
        print("\n✓ Setup complete!")
        print("\nNext steps:")
        print("  1. Commit changes: git add -A && git commit -m 'Add CI pipeline and dashboard'")
        print("  2. Push to GitHub: git push origin main")
        print("  3. Check GitHub Actions tab to see workflows running")
    except Exception as e:
        print(f"✗ Setup failed: {e}")
        raise


if __name__ == '__main__':
    main()
