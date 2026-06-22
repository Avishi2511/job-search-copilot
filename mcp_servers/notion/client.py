"""
Thin wrapper around the Notion API for job tracker operations.
"""

import os
from datetime import date
from notion_client import Client


def _notion() -> Client:
    return Client(auth=os.environ["NOTION_API_TOKEN"])


# ---------------------------------------------------------------------------
# One-time setup
# ---------------------------------------------------------------------------

def setup_database(parent_page_id: str) -> str:
    """
    Creates the Jobs database inside the given Notion page.
    Returns the new database ID — save it as NOTION_DATABASE_ID in .env.
    """
    notion = _notion()
    response = notion.databases.create(
        parent={"type": "page_id", "page_id": parent_page_id},
        title=[{"type": "text", "text": {"content": "Job Search Tracker"}}],
        properties={
            "Name": {"title": {}},
            "Company": {"rich_text": {}},
            "Status": {
                "select": {
                    "options": [
                        {"name": "New",       "color": "blue"},
                        {"name": "Reviewed",  "color": "yellow"},
                        {"name": "Contacted", "color": "orange"},
                        {"name": "Replied",   "color": "green"},
                        {"name": "Rejected",  "color": "red"},
                    ]
                }
            },
            "Source":           {"select": {"options": [
                {"name": "adzuna",   "color": "purple"},
                {"name": "remotive", "color": "pink"},
            ]}},
            "Location":         {"rich_text": {}},
            "URL":              {"url": {}},
            "Date Posted":      {"date": {}},
            "Contacts Found":   {"rich_text": {}},
            "Outreach Message": {"rich_text": {}},
            "Date Added":       {"date": {}},
        },
    )
    return response["id"].replace("-", "")


# ---------------------------------------------------------------------------
# Property builders
# ---------------------------------------------------------------------------

def _title(text: str) -> dict:
    return {"title": [{"text": {"content": text[:2000]}}]}

def _rich_text(text: str) -> dict:
    return {"rich_text": [{"text": {"content": text[:2000]}}]}

def _select(name: str) -> dict:
    return {"select": {"name": name}}

def _url(link: str) -> dict:
    return {"url": link or None}

def _date(iso_str: str) -> dict:
    if iso_str:
        return {"date": {"start": iso_str}}
    return {"date": None}

def _format_contacts(contacts: list[dict]) -> str:
    if not contacts:
        return ""
    lines = []
    for c in contacts:
        line = f"{c.get('name', '')} ({c.get('role', '')})"
        if c.get("profile_url"):
            line += f" — {c['profile_url']}"
        lines.append(line)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Core operations
# ---------------------------------------------------------------------------

def create_job_entry(job: dict) -> str:
    """Creates a single job page in the Notion database. Returns the page ID."""
    notion = _notion()
    database_id = os.environ["NOTION_DATABASE_ID"]

    page = notion.pages.create(
        parent={"database_id": database_id},
        properties={
            "Name":             _title(job.get("title", "Untitled")),
            "Company":          _rich_text(job.get("company", "")),
            "Status":           _select("New"),
            "Source":           _select(job.get("source", "unknown")),
            "Location":         _rich_text(job.get("location", "")),
            "URL":              _url(job.get("url", "")),
            "Date Posted":      _date(job.get("date_posted", "")),
            "Contacts Found":   _rich_text(_format_contacts(job.get("contacts", []))),
            "Outreach Message": _rich_text(job.get("outreach_message", "")),
            "Date Added":       _date(date.today().isoformat()),
        },
    )
    return page["id"]


def bulk_sync_jobs(jobs: list[dict]) -> dict:
    """Creates Notion pages for a list of jobs. Returns a summary."""
    created = 0
    failed = 0

    for job in jobs:
        try:
            create_job_entry(job)
            created += 1
            print(f"[notion] Created: {job.get('title')} @ {job.get('company')}")
        except Exception as e:
            failed += 1
            print(f"[notion] Failed: {job.get('title')} @ {job.get('company')} — {e}")

    return {"created": created, "failed": failed}


def log_outreach(page_id: str, contact_name: str, message: str) -> None:
    """Updates the Outreach Message field and sets status to Contacted."""
    notion = _notion()
    notion.pages.update(
        page_id=page_id,
        properties={
            "Outreach Message": _rich_text(message),
            "Status":           _select("Contacted"),
        },
    )
