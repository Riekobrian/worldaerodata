#!/usr/bin/env python3
"""
Dashboard generator for flight pipeline run metrics.
Queries pipeline_runs table and generates an HTML dashboard showing trends.
"""

import json
import os
from datetime import datetime
from pathlib import Path

import psycopg


def get_db_connection():
    """Get PostgreSQL connection from DSN."""
    dsn = os.environ.get('FLIGHT_PIPELINE_DB_DSN')
    if not dsn:
        raise ValueError("FLIGHT_PIPELINE_DB_DSN environment variable not set")
    return psycopg.connect(dsn)


def fetch_pipeline_runs(limit=20):
    """Fetch recent pipeline runs from database."""
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    source_name,
                    status,
                    dry_run,
                    records_in,
                    records_ok,
                    records_failed,
                    message,
                    started_at,
                    finished_at
                FROM pipeline_runs
                ORDER BY started_at DESC
                LIMIT %s
            """, (limit,))
            
            columns = [desc[0] for desc in cur.description]
            runs = []
            for row in cur.fetchall():
                runs.append(dict(zip(columns, row)))
        
        conn.close()
        return runs
    except Exception as e:
        print(f"Warning: Could not fetch pipeline runs: {e}")
        return []


def calculate_duration(run):
    """Calculate duration in seconds from timestamps."""
    if run['started_at'] and run['finished_at']:
        delta = run['finished_at'] - run['started_at']
        return delta.total_seconds()
    return None


def generate_html_dashboard(runs):
    """Generate HTML dashboard from pipeline runs."""
    # Calculate stats
    total_runs = len(runs)
    successful_runs = sum(1 for r in runs if r['status'] == 'success')
    failed_runs = sum(1 for r in runs if r['status'] == 'failed')
    partial_success_runs = sum(1 for r in runs if r['status'] == 'partial_success')
    
    total_records = sum(r['records_in'] for r in runs)
    total_valid = sum(r['records_ok'] for r in runs)
    total_failed = sum(r['records_failed'] for r in runs)
    
    success_rate = (total_valid / total_records * 100) if total_records > 0 else 0
    
    # Generate run rows
    run_rows = ""
    for run in runs:
        duration = calculate_duration(run)
        duration_str = f"{duration:.1f}s" if duration else "N/A"
        
        status_badge = f'<span class="badge badge-{run["status"]}">{run["status"]}</span>'
        
        run_rows += f"""
        <tr>
            <td>{run['id']}</td>
            <td>{run['source_name']}</td>
            <td>{status_badge}</td>
            <td>{'Yes' if run['dry_run'] else 'No'}</td>
            <td>{run['records_in']}</td>
            <td>{run['records_ok']}</td>
            <td>{run['records_failed']}</td>
            <td>{duration_str}</td>
            <td>{run['started_at'].strftime('%Y-%m-%d %H:%M:%S') if run['started_at'] else 'N/A'}</td>
        </tr>
        """
    
    # Generate chart data (last 10 runs)
    recent_runs = runs[:10]
    chart_labels = json.dumps([r['id'] for r in reversed(recent_runs)])
    chart_success = json.dumps([r['records_ok'] for r in reversed(recent_runs)])
    chart_failed = json.dumps([r['records_failed'] for r in reversed(recent_runs)])
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Flight Pipeline Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
            padding: 30px;
        }}
        
        h1 {{
            color: #333;
            margin-bottom: 10px;
            text-align: center;
        }}
        
        .timestamp {{
            text-align: center;
            color: #999;
            font-size: 0.9em;
            margin-bottom: 30px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        
        .stat-card .label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }}
        
        .stat-card .value {{
            font-size: 2em;
            font-weight: bold;
        }}
        
        .chart-section {{
            margin-bottom: 40px;
        }}
        
        .chart-section h2 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.2em;
        }}
        
        .chart-container {{
            position: relative;
            height: 400px;
            margin-bottom: 20px;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        
        table th {{
            background: #f5f5f5;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #ddd;
        }}
        
        table td {{
            padding: 10px 12px;
            border-bottom: 1px solid #eee;
        }}
        
        table tr:hover {{
            background: #f9f9f9;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        
        .badge-success {{
            background: #d4edda;
            color: #155724;
        }}
        
        .badge-failed {{
            background: #f8d7da;
            color: #721c24;
        }}
        
        .badge-partial_success {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .section-title {{
            color: #333;
            margin-top: 40px;
            margin-bottom: 20px;
            font-size: 1.2em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        
        .no-data {{
            text-align: center;
            color: #999;
            padding: 40px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>✈️ Flight Pipeline Dashboard</h1>
        <div class="timestamp">Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="label">Total Runs</div>
                <div class="value">{total_runs}</div>
            </div>
            <div class="stat-card">
                <div class="label">Successful</div>
                <div class="value">{successful_runs}</div>
            </div>
            <div class="stat-card">
                <div class="label">Failed</div>
                <div class="value">{failed_runs}</div>
            </div>
            <div class="stat-card">
                <div class="label">Records Processed</div>
                <div class="value">{total_records:,}</div>
            </div>
            <div class="stat-card">
                <div class="label">Success Rate</div>
                <div class="value">{success_rate:.1f}%</div>
            </div>
        </div>
        
        <div class="chart-section">
            <h2>Record Processing Trend (Last 10 Runs)</h2>
            <div class="chart-container">
                <canvas id="trendChart"></canvas>
            </div>
        </div>
        
        <div class="section-title">Run History</div>
        {'<table><thead><tr><th>ID</th><th>Source</th><th>Status</th><th>Dry Run</th><th>Records In</th><th>Records OK</th><th>Records Failed</th><th>Duration</th><th>Started At</th></tr></thead><tbody>' + run_rows + '</tbody></table>' if run_rows else '<div class="no-data">No pipeline runs recorded yet.</div>'}
    </div>
    
    <script>
        const ctx = document.getElementById('trendChart').getContext('2d');
        new Chart(ctx, {{
            type: 'bar',
            data: {{
                labels: {chart_labels},
                datasets: [
                    {{
                        label: 'Records OK',
                        data: {chart_success},
                        backgroundColor: 'rgba(78, 205, 196, 0.8)',
                        borderColor: 'rgb(78, 205, 196)',
                        borderWidth: 1
                    }},
                    {{
                        label: 'Records Failed',
                        data: {chart_failed},
                        backgroundColor: 'rgba(255, 107, 107, 0.8)',
                        borderColor: 'rgb(255, 107, 107)',
                        borderWidth: 1
                    }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        stacked: false
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: true,
                        position: 'top'
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    return html


def main():
    """Main entry point."""
    import sys
    
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('dashboard.html')
    
    print(f"Fetching pipeline runs...")
    runs = fetch_pipeline_runs(limit=20)
    
    if not runs:
        print("No pipeline runs found in database.")
        return
    
    print(f"Generating dashboard with {len(runs)} runs...")
    html = generate_html_dashboard(runs)
    
    output_path.write_text(html)
    print(f"Dashboard generated: {output_path}")


if __name__ == '__main__':
    main()
