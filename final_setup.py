#!/usr/bin/env python3
"""
FINAL SETUP SCRIPT - Run this to complete deployment setup
Creates all necessary files and directories for CI/CD and dashboard
"""

import sys
from pathlib import Path

def setup():
    """Complete setup process."""
    repo_root = Path(__file__).parent
    
    print("=" * 70)
    print("FLIGHT PIPELINE: FINAL SETUP")
    print("=" * 70)
    print()
    
    # Step 1: Create .github/workflows
    print("Step 1: Creating .github/workflows directory...")
    workflows_dir = repo_root / '.github' / 'workflows'
    workflows_dir.mkdir(parents=True, exist_ok=True)
    print(f"✓ Created: {workflows_dir.relative_to(repo_root)}")
    
    # Step 2: Create ci.yml
    print("\nStep 2: Creating GitHub Actions workflow...")
    ci_yml = workflows_dir / 'ci.yml'
    ci_yaml_content = """name: CI Pipeline

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
    ci_yml.write_text(ci_yaml_content)
    print(f"✓ Created: {ci_yml.relative_to(repo_root)}")
    
    # Step 3: Verify dashboard generator exists
    print("\nStep 3: Verifying dashboard generator...")
    dashboard_gen = repo_root / 'utils' / 'generate_dashboard.py'
    if dashboard_gen.exists():
        print(f"✓ Found: {dashboard_gen.relative_to(repo_root)}")
    else:
        print(f"✗ Missing: {dashboard_gen.relative_to(repo_root)}")
        return False
    
    # Step 4: Verify pyproject.toml updated
    print("\nStep 4: Verifying pyproject.toml...")
    pyproject = repo_root / 'pyproject.toml'
    content = pyproject.read_text()
    if 'pytest' in content and 'ruff' in content:
        print(f"✓ Dev dependencies added to pyproject.toml")
    else:
        print(f"✗ Dev dependencies not found in pyproject.toml")
        return False
    
    # Step 5: Verify run_ingestion.py integration
    print("\nStep 5: Verifying dashboard integration...")
    run_ingest = repo_root / 'pipelines' / 'run_ingestion.py'
    content = run_ingest.read_text()
    if 'generate_html_dashboard' in content:
        print(f"✓ Dashboard generation integrated")
    else:
        print(f"⚠ Dashboard generation may not be integrated")
    
    return True

def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "=" * 70)
    print("SETUP COMPLETE ✓")
    print("=" * 70)
    print()
    print("Next steps to deploy to GitHub:")
    print()
    print("1. Install dev dependencies:")
    print("   pip install -e \".[dev]\"")
    print()
    print("2. Test locally (optional but recommended):")
    print("   pytest flight_pipeline/tests/ -v")
    print("   ruff check flight_pipeline/")
    print("   python pipelines/run_ingestion.py --source all --dry-run")
    print()
    print("3. Commit all changes:")
    print("   git add -A")
    print("   git commit -m \"Add CI pipeline and dashboard infrastructure\"")
    print()
    print("4. Push to GitHub:")
    print("   git remote add origin https://github.com/Riekobrian/worldaerodata.git")
    print("   git branch -M main")
    print("   git push -u origin main")
    print()
    print("5. Monitor GitHub Actions:")
    print("   - Go to: https://github.com/Riekobrian/worldaerodata/actions")
    print("   - Watch workflows run on each push/PR")
    print()
    print("6. View dashboard after pipeline runs:")
    print("   - After running: python pipelines/run_ingestion.py --source all")
    print("   - Open: dashboard.html in web browser")
    print()
    print("Documentation:")
    print("  - DEPLOYMENT_GUIDE.md        - Complete setup guide")
    print("  - IMPLEMENTATION_COMPLETE.md - What was implemented")
    print("  - README.md                  - Project overview")
    print()

if __name__ == '__main__':
    try:
        if setup():
            print_next_steps()
            sys.exit(0)
        else:
            print("\n✗ Setup failed. Please check the errors above.")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Setup error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
