"""
One-time script to migrate data from SQLite to PostgreSQL.
Run once with: python migrate_sqlite_to_pg.py
"""
import sqlite3
import os

from dotenv import load_dotenv
load_dotenv()

from app import create_app
from extensions import db

SQLITE_PATH = 'instance/plataforma.db'

# Tables in dependency order (parents before children)
TABLES = [
    'iste_standard',
    'material',
    'rubric_bank_item',
    'training_course',
    'course_module',
    'resource',
    'user',
    'learning_experience',
    'learning_experience_iste',
    'learning_experience_requirement',
    'comment',
    'learning_experience_rubric',
    'learning_experience_evaluation',
    'learning_experience_evaluation_score',
    'course_teacher',
    'project_manual',
    'project_manual_theme',
    'weekly_plan',
    'manual_session_plan',
    'project_rubric',
    'project_rubric_criterion',
]


def migrate():
    if not os.path.exists(SQLITE_PATH):
        print(f'SQLite DB not found at {SQLITE_PATH}')
        return

    sqlite_conn = sqlite3.connect(SQLITE_PATH)
    sqlite_conn.row_factory = sqlite3.Row

    app = create_app()
    with app.app_context():
        pg_conn = db.engine.raw_connection()
        pg_cur = pg_conn.cursor()

        for table in TABLES:
            cur = sqlite_conn.cursor()
            try:
                cur.execute(f'SELECT * FROM {table}')
            except sqlite3.OperationalError:
                print(f'  {table}: missing in SQLite, skipping')
                continue
            rows = cur.fetchall()
            if not rows:
                print(f'  {table}: empty, skipping')
                continue

            columns = [description[0] for description in cur.description]

            # Detect boolean columns from PostgreSQL schema
            pg_cur.execute(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_name = %s AND data_type = 'boolean'",
                (table,)
            )
            bool_cols = {r[0] for r in pg_cur.fetchall()}
            bool_indices = {i for i, c in enumerate(columns) if c in bool_cols}

            def convert_row(row):
                row = list(row)
                for i in bool_indices:
                    if row[i] is not None:
                        row[i] = bool(row[i])
                return tuple(row)

            placeholders = ', '.join(['%s'] * len(columns))
            col_names = ', '.join(f'"{c}"' for c in columns)
            insert_sql = f'INSERT INTO "{table}" ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING'

            data = [convert_row(row) for row in rows]
            pg_cur.executemany(insert_sql, data)

            # Reset sequence for tables with serial PKs
            if 'id' in columns:
                pg_cur.execute(
                    f"SELECT setval(pg_get_serial_sequence('\"{table}\"', 'id'), "
                    f"COALESCE((SELECT MAX(id) FROM \"{table}\"), 1))"
                )

            print(f'  {table}: {len(rows)} rows migrated')

        pg_conn.commit()
        pg_cur.close()
        pg_conn.close()

    sqlite_conn.close()
    print('\nMigration complete!')


if __name__ == '__main__':
    migrate()
