import os
import requests
from typing import Optional
from .schema import Job

ADZUNA_BASE_URL = "https://api.adzuna.com/v1/api/jobs/in/search"


def fetch_adzuna_jobs(query: str, location: str = "India", max_results: int = 50) -> list[Job]:
    app_id = os.environ["ADZUNA_APP_ID"]
    api_key = os.environ["ADZUNA_API_KEY"]

    jobs: list[Job] = []
    page = 1
    results_per_page = min(max_results, 50)

    while len(jobs) < max_results:
        response = requests.get(
            f"{ADZUNA_BASE_URL}/{page}",
            params={
                "app_id": app_id,
                "app_key": api_key,
                "what": query,
                "where": location,
                "results_per_page": results_per_page,
                "content-type": "application/json",
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        raw_jobs = data.get("results", [])
        if not raw_jobs:
            break

        for raw in raw_jobs:
            jobs.append(_normalize(raw))
            if len(jobs) >= max_results:
                break

        if len(raw_jobs) < results_per_page:
            break
        page += 1

    return jobs


def _normalize(raw: dict) -> Job:
    return Job(
        title=raw.get("title", "").strip(),
        company=raw.get("company", {}).get("display_name", "Unknown"),
        description=raw.get("description", "").strip(),
        location=raw.get("location", {}).get("display_name", "India"),
        url=raw.get("redirect_url", ""),
        source="adzuna",
        date_posted=raw.get("created", "")[:10] if raw.get("created") else None,
    )
