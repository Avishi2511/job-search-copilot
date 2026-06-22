import re
import json
import os
from langchain_google_genai import ChatGoogleGenerativeAI

from pipeline.config import load_config
from pipeline.state import PipelineState

_HTML_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _HTML_TAG_RE.sub(" ", text).strip()


def _passes_rules(job: dict, config: dict) -> bool:
    title = job.get("title", "").lower()
    location = job.get("location", "").lower()

    # Drop immediately if a blocked keyword appears in the title
    for kw in config["roles"]["blocked_keywords"]:
        if kw.lower() in title:
            return False

    # Must match at least one allowed role keyword in the title
    role_match = any(kw.lower() in title for kw in config["roles"]["allowed_keywords"])

    # Must match at least one allowed location
    location_match = any(loc.lower() in location for loc in config["location"]["allowed_locations"])

    return role_match and location_match


def _gemini_filter(jobs: list[dict], config: dict) -> list[dict]:
    if not jobs:
        return []

    llm = ChatGoogleGenerativeAI(
        model=config["llm"]["model"],
        temperature=config["llm"]["temperature"],
        google_api_key=os.environ["GEMINI_API_KEY"],
    )

    # Build a concise job list for the prompt (avoid sending full HTML descriptions)
    job_lines = []
    for i, job in enumerate(jobs, start=1):
        desc_snippet = _strip_html(job.get("description", ""))[:300]
        job_lines.append(f'{i}. Title: "{job["title"]}" | Company: {job["company"]} | Desc: {desc_snippet}')

    prompt = f"""You are filtering job listings for an AI/ML software engineer job search.

KEEP a job if it is clearly an engineering or technical role related to:
AI, ML, LLM, NLP, Generative AI, Deep Learning, or software engineering in an AI-heavy context.

REMOVE a job if it is: HR, Recruiter, Sales, Marketing, Finance, Business Analyst,
Data Analyst (non-ML), Customer Support, or any non-technical role.

Jobs to evaluate:
{chr(10).join(job_lines)}

Return ONLY valid JSON — a list of objects with "index" (1-based) and "keep" (true/false).
Example: [{{"index": 1, "keep": true}}, {{"index": 2, "keep": false}}]"""

    response = llm.invoke(prompt)
    raw = response.content.strip()

    # Strip markdown fences if Gemini wraps the response
    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw, flags=re.MULTILINE).strip()

    try:
        decisions = json.loads(raw)
        keep_indices = {d["index"] for d in decisions if d.get("keep")}
        return [job for i, job in enumerate(jobs, start=1) if i in keep_indices]
    except (json.JSONDecodeError, KeyError):
        # If Gemini response can't be parsed, fall back to keeping all rule-passed jobs
        print("[filter] Warning: Gemini response could not be parsed — keeping all rule-passed jobs")
        return jobs


async def filter_node(state: PipelineState) -> dict:
    config = load_config()
    raw_jobs = state["raw_jobs"]

    # Step 1: rule-based pre-filter (fast, no API call)
    rule_passed = [j for j in raw_jobs if _passes_rules(j, config)]
    print(f"[filter] Rule filter: {len(raw_jobs)} → {len(rule_passed)} jobs")

    # Step 2: Gemini relevance check on remaining jobs
    filtered = _gemini_filter(rule_passed, config)
    print(f"[filter] Gemini filter: {len(rule_passed)} → {len(filtered)} jobs")

    return {"filtered_jobs": filtered}
