from utils.db import Database

def check_pipeline_runs_schema():
    db = Database.from_env()
    with db.session() as session:
        with session._conn.cursor() as cur:
            cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'pipeline_runs'")
            columns = [row[0] for row in cur.fetchall()]
            print("Columns in pipeline_runs table:", columns)

if __name__ == "__main__":
    check_pipeline_runs_schema()