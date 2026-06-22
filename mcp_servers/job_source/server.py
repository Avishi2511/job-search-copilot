"""
Job Source MCP Server

Run with:
  python -m mcp_servers.job_source.server

Tools exposed:
  fetch_adzuna_jobs(query, location, max_results)
  fetch_remotive_jobs(query, max_results)
  fetch_all_jobs(query, location, max_results_per_source)
"""

import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .adzuna import fetch_adzuna_jobs
from .remotive import fetch_remotive_jobs
from .schema import Job

load_dotenv()

mcp = FastMCP("job-source")


@mcp.tool()
def get_adzuna_jobs(query: str, location: str = "India", max_results: int = 50) -> list[dict]:
    """Fetch jobs from Adzuna (India-focused). Returns normalized job objects."""
    jobs = fetch_adzuna_jobs(query=query, location=location, max_results=max_results)
    return [j.model_dump() for j in jobs]


@mcp.tool()
def get_remotive_jobs(query: str, max_results: int = 50) -> list[dict]:
    """Fetch remote tech jobs from Remotive. Returns normalized job objects."""
    jobs = fetch_remotive_jobs(query=query, max_results=max_results)
    return [j.model_dump() for j in jobs]


@mcp.tool()
def get_all_jobs(query: str, location: str = "India", max_results_per_source: int = 50) -> list[dict]:
    """Fetch jobs from all sources (Adzuna + Remotive) and return a combined normalized list."""
    results: list[Job] = []

    try:
        results.extend(fetch_adzuna_jobs(query=query, location=location, max_results=max_results_per_source))
    except Exception as e:
        print(f"[job-source] Adzuna fetch failed: {e}")

    try:
        results.extend(fetch_remotive_jobs(query=query, max_results=max_results_per_source))
    except Exception as e:
        print(f"[job-source] Remotive fetch failed: {e}")

    return [j.model_dump() for j in results]


if __name__ == "__main__":
    mcp.run()
