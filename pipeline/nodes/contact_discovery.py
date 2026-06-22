import os
import json
import re
from tavily import TavilyClient
from langchain_google_genai import ChatGoogleGenerativeAI

from pipeline.config import load_config
from pipeline.state import PipelineState


def _build_search_query(company: str, target_roles: list[str]) -> str:
    roles_str = " OR ".join(f'"{r}"' for r in target_roles[:4])
    return f'"{company}" ({roles_str}) AI engineer hiring'


def _search_contacts(company: str, config: dict) -> list[dict]:
    client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])
    target_roles = config["contact_discovery"]["target_roles"]
    query = _build_search_query(company, target_roles)

    try:
        response = client.search(
            query=query,
            search_depth="basic",
            max_results=5,
        )
    except Exception as e:
        print(f"[contact_discovery] Tavily search failed for '{company}': {e}")
        return []

    results = response.get("results", [])
    if not results:
        return []

    # Build a compact context string from search snippets
    snippets = []
    for r in results:
        title = r.get("title", "")
        content = r.get("content", "")[:400]
        url = r.get("url", "")
        snippets.append(f"Source: {title} ({url})\n{content}")

    return _extract_contacts_with_gemini(company, "\n\n".join(snippets), config)


def _extract_contacts_with_gemini(company: str, search_context: str, config: dict) -> list[dict]:
    llm = ChatGoogleGenerativeAI(
        model=config["llm"]["model"],
        temperature=0,
        google_api_key=os.environ["GEMINI_API_KEY"],
    )
    max_contacts = config["contact_discovery"]["max_contacts_per_company"]
    target_roles = ", ".join(config["contact_discovery"]["target_roles"])

    prompt = f"""From the web search results below about "{company}", extract real people who are likely involved in hiring AI/ML engineers.

Look for: {target_roles}.
Only include people with a clearly identified name and role. Ignore generic job postings.
Return at most {max_contacts} people.

Search results:
{search_context}

Return ONLY valid JSON — a list of objects with "name", "role", and "profile_url" (use empty string if no URL found).
Example: [{{"name": "Jane Smith", "role": "Engineering Manager", "profile_url": "https://..."}}]
If no relevant people are found, return an empty list []."""

    response = llm.invoke(prompt)
    raw = response.content.strip()

    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()

    try:
        contacts = json.loads(raw)
        return contacts if isinstance(contacts, list) else []
    except json.JSONDecodeError:
        return []


async def contact_discovery_node(state: PipelineState) -> dict:
    config = load_config()
    jobs = state["new_jobs"]

    # Search once per unique company to save Tavily API calls
    company_contacts: dict[str, list[dict]] = {}

    for job in jobs:
        company = job.get("company", "Unknown")
        if company not in company_contacts:
            print(f"[contact_discovery] Searching contacts for: {company}")
            company_contacts[company] = _search_contacts(company, config)
            found = len(company_contacts[company])
            print(f"[contact_discovery]   → {found} contact(s) found")

    jobs_with_contacts = []
    for job in jobs:
        enriched = dict(job)
        enriched["contacts"] = company_contacts.get(job.get("company", ""), [])
        jobs_with_contacts.append(enriched)

    total_contacts = sum(len(j["contacts"]) for j in jobs_with_contacts)
    print(f"[contact_discovery] Done. {total_contacts} contacts found across {len(jobs)} jobs.")
    return {"jobs_with_contacts": jobs_with_contacts}
