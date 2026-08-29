import os
from pathlib import Path

from psycopg.rows import dict_row
from psycopg.types.json import Json
from psycopg_pool import ConnectionPool

from backend.utils.utils import Job, JobStatus, Report

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")

DB_POOL = ConnectionPool(
    DATABASE_URL,
    min_size=1,
    max_size=10,
    kwargs={"row_factory": dict_row},
    open=False,
)
    
class Database:
    def __init__(self):
        self.pool = DB_POOL
        try:
            self.pool.open()
            self.pool.wait(timeout=10)   
        except Exception as exc:
            raise RuntimeError(f"cannot connect to Postgres: {exc}") from exc

    def get_connection(self):
        """Borrow a connection from the pool. Use inside a `with` block."""
        return self.pool.connection()

    def init_schema(self, sql_path: Path | None = None) -> None:
        """Create the tables if they are not there yet.

        Every statement in table.sql uses IF NOT EXISTS, so this is safe
        to run on every startup.
        """
        sql_path = sql_path or Path(__file__).parent / "table.sql"
        sql = sql_path.read_text()
        with self.get_connection() as conn, conn.cursor() as cur:
            cur.execute(sql)
            conn.commit()

    def close(self):
        self.pool.close()


class DatabaseOperations:
    def __init__(self):
        self.db = Database()

    @staticmethod
    def _to_job(row: dict) -> Job:
        """Turn a database row into a Job.

        The report column is JSONB, so it comes back as a plain dict.
        It becomes a Report here and stays one everywhere above this
        line -- dicts do not leave the database layer.
        """
        row = dict(row)
        raw = row.get("report")
        row["report"] = Report.model_validate(raw) if raw is not None else None
        # psycopg hands back a uuid.UUID for a uuid column, but Job.id is
        # declared str and everything above treats it as one. Coerce here
        # so the type hint is not a lie.
        row["id"] = str(row["id"])
        return Job(**row)
        
    def get_job(self, job_id: str):
        query = "SELECT * FROM jobs WHERE id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (job_id,))
                result = cur.fetchone()
                if result:
                    return self._to_job(result)
                else:
                    return None
     
    def get_job_history(self, limit: int = 50, offset: int = 0):
        query = "SELECT * FROM jobs ORDER BY created_at DESC LIMIT %s OFFSET %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (limit, offset))
                results = cur.fetchall()
                return [self._to_job(row) for row in results]
            
    def create_job(self, job: Job):
        query = """
        INSERT INTO jobs (
            id, status, model, upload_path, container_id,
            created_at, started_at, finished_at, error, report
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (
                    job.id,
                    job.status,
                    job.model,
                    job.upload_path,
                    job.container_id,
                    job.created_at,
                    job.started_at,
                    job.finished_at,
                    job.error,
                    Json(job.report.model_dump(mode="json")) if job.report else None
                ))
                conn.commit()
    
    def job_failed(self, job_id: str, error_message: str):
        query = "UPDATE jobs SET status = %s, error = %s WHERE id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (JobStatus.FAILED.value, error_message, job_id))
                conn.commit()
                
    def job_succeeded(self, job_id: str, report: Report):
        query = "UPDATE jobs SET status = %s, report = %s WHERE id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                # Json() tells psycopg this is JSONB, not a broken parameter.
                cur.execute(
                    query,
                    (JobStatus.SUCCEEDED.value, Json(report.model_dump(mode="json")), job_id),
                )
                conn.commit()                                 
                
    def job_started(self, job_id: str, container_id: str):
        """Job handed off to a container: record which one, and when."""
        query = """
        UPDATE jobs
           SET status = %s, container_id = %s, started_at = NOW()
         WHERE id = %s
        """
        with self.db.get_connection() as conn, conn.cursor() as cur:
            cur.execute(query, (JobStatus.RUNNING.value, container_id, job_id))
            conn.commit()

    def job_running(self, job_id: str):
        query = "UPDATE jobs SET status = %s WHERE id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (JobStatus.RUNNING.value, job_id))
                conn.commit()            
                    
    def job_timed_out(self, job_id: str):
        query = "UPDATE jobs SET status = %s WHERE id = %s"
        with self.db.get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(query, (JobStatus.TIMED_OUT.value, job_id))
                conn.commit()           