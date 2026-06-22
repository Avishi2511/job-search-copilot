import os
import re
from langchain_google_genai import ChatGoogleGenerativeAI

from pipeline.config import load_config
from pipeline.state import PipelineState


def _generate_message(job: dict, config: dict, llm: ChatGoogleGenerativeAI) -> str:
    profile = config["profile"]
    msg_cfg = config["message"]

    contacts = job.get("contacts", [])
    contact_name = contacts[0]["name"] if contacts else None
    contact_role = contacts[0]["role"] if contacts else None

    greeting = f"Hi {contact_name.split()[0]}," if contact_name else "Hi there,"
    contact_context = (
        f"Contact: {contact_name} ({contact_role})"
        if contact_name
        else "No specific contact — write a general cold outreach."
    )

    skills_str = ", ".join(msg_cfg["highlight_skills"])

    prompt = f"""Write a short, personalized cold outreach message for a job application.

Sender profile:
- Name: {profile["name"]}
- Current role: {profile["current_role"]}
- Bio: {profile["bio"].strip()}
- Key skills to highlight: {skills_str}

Job details:
- Title: {job["title"]}
- Company: {job["company"]}
- {contact_context}

Requirements:
- Start with: {greeting}
- Tone: {msg_cfg["tone"]}
- Max length: {msg_cfg["max_length_words"]} words
- Sign off with: {msg_cfg["sign_off"]}, {profile["name"]}
- Do NOT use generic filler phrases like "I hope this finds you well"
- Be specific about the role and one relevant skill

Return only the message text, no extra commentary."""

    response = llm.invoke(prompt)
    return response.content.strip()


async def message_generation_node(state: PipelineState) -> dict:
    config = load_config()
    jobs = state["jobs_with_contacts"]

    llm = ChatGoogleGenerativeAI(
        model=config["llm"]["model"],
        temperature=0.4,  # slight creativity for message variety
        google_api_key=os.environ["GEMINI_API_KEY"],
    )

    final_jobs = []
    for i, job in enumerate(jobs, start=1):
        print(f"[message_generation] Generating message {i}/{len(jobs)}: {job['title']} @ {job['company']}")
        message = _generate_message(job, config, llm)
        enriched = dict(job)
        enriched["outreach_message"] = message
        final_jobs.append(enriched)

    print(f"[message_generation] Done. {len(final_jobs)} messages generated.")
    return {"final_jobs": final_jobs}
