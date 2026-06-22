"""
Notion MCP Server

Run with:
  python -m mcp_servers.notion.server

Tools exposed:
  setup_notion_database(parent_page_id)
  create_notion_job(job)
  bulk_sync_to_notion(jobs)
  log_notion_outreach(page_id, contact_name, message)
"""

import os
from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .client import setup_database, create_job_entry, bulk_sync_jobs, log_outreach

load_dotenv()

mcp = FastMCP("notion")


@mcp.tool()
def setup_notion_database(parent_page_id: str) -> str:
    """
    One-time setup: creates the Job Search Tracker database inside the given
    Notion page. Returns the database ID — save it as NOTION_DATABASE_ID in .env.
    """
    db_id = setup_database(parent_page_id)
    return f"Database created. Add this to your .env:\nNOTION_DATABASE_ID={db_id}"


@mcp.tool()
def create_notion_job(job: dict) -> str:
    """Creates a single job entry in the Notion Jobs database. Returns the Notion page ID."""
    page_id = create_job_entry(job)
    return page_id


@mcp.tool()
def bulk_sync_to_notion(jobs: list[dict]) -> dict:
    """
    Syncs a list of jobs to Notion. Each job becomes a page in the Jobs database
    with status set to 'New'. Returns a summary with created and failed counts.
    """
    return bulk_sync_jobs(jobs)


@mcp.tool()
def log_notion_outreach(page_id: str, contact_name: str, message: str) -> str:
    """
    Updates a Notion job page with an outreach message and sets its status to 'Contacted'.
    """
    log_outreach(page_id=page_id, contact_name=contact_name, message=message)
    return f"Updated page {page_id} — status set to Contacted."


if __name__ == "__main__":
    mcp.run()
