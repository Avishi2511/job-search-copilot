import requests
from .schema import Job

REMOTIVE_BASE_URL = "https://remotive.com/api/remote-jobs"

# Remotive categories that are relevant to AI/ML roles
RELEVANT_CATEGORIES = [
    "software-dev",
    "data",
    "machine-learning",
]


def fetch_remotive_jobs(query: str, max_results: int = 50) -> list[Job]:
    jobs: list[Job] = []

    for category in RELEVANT_CATEGORIES:
        if len(jobs) >= max_results:
            break

        response = requests.get(
            REMOTIVE_BASE_URL,
            params={
                "category": category,
                "search": query,
                "limit": max_results,
            },
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        for raw in data.get("jobs", []):
            jobs.append(_normalize(raw))
            if len(jobs) >= max_results:
                break

    return jobs


def _normalize(raw: dict) -> Job:
    return Job(
        title=raw.get("title", "").strip(),
        company=raw.get("company_name", "Unknown"),
        description=raw.get("description", "").strip(),
        location=raw.get("candidate_required_location", "Remote"),
        url=raw.get("url", ""),
        source="remotive",
        date_posted=raw.get("publication_date", "")[:10] if raw.get("publication_date") else None,
    )
