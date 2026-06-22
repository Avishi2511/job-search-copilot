import os
import psycopg2

from pipeline.config import load_config
from pipeline.state import PipelineState


def _make_dedup_key(job: dict) -> str:
    company = job.get("company", "").lower().strip()
    title = job.get("title", "").lower().strip()
    return f"{company}::{title}"


async def dedup_node(state: PipelineState) -> dict:
    config = load_config()
    jobs = state["filtered_jobs"]
    top_n = config["jobs"]["top_n"]

    conn = psycopg2.connect(os.environ["POSTGRES_URL"])
    new_jobs: list[dict] = []

    try:
        with conn:
            with conn.cursor() as cur:
                for job in jobs:
                    key = _make_dedup_key(job)
                    cur.execute("SELECT 1 FROM seen_jobs WHERE dedup_key = %s", (key,))
                    if cur.fetchone() is None:
                        new_jobs.append(job)
                        cur.execute(
                            """
                            INSERT INTO seen_jobs (dedup_key, company, title, source, url)
                            VALUES (%s, %s, %s, %s, %s)
                            """,
                            (key, job["company"], job["title"], job["source"], job.get("url", "")),
                        )
    finally:
        conn.close()

    # Respect top_n limit
    new_jobs = new_jobs[:top_n]
    print(f"[dedup] New jobs after deduplication: {len(new_jobs)} (capped at {top_n})")
    return {"new_jobs": new_jobs}
