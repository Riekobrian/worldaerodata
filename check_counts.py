import os
import sys
from pathlib import Path
from utils.db import Database

# Load environment variables
project_root = Path(__file__).resolve().parent
env_path = project_root / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, val = line.split('=', 1)
                os.environ[key.strip()] = val.strip().strip('"').strip("'")

db = Database.from_env()

with db.session() as session:
    with session._conn.cursor() as cur:
        # Check row counts
        tables = ['airports', 'airlines', 'routes', 'flight_offers']
        for t in tables:
            cur.execute(f'SELECT COUNT(*) FROM {t}')
            count = cur.fetchone()[0]
            print(f'{t}: {count:,} rows')

        try:
            cur.execute("SELECT MIN(started_at), MAX(started_at), COUNT(*) FROM pipeline_runs")
            run = cur.fetchone()
            print(f'pipeline_runs: {run[2]} runs ({run[0]} to {run[1]})')
        except Exception as e:
            print(f'pipeline_runs: table not found or error: {e}')