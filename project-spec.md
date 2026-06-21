# 🧠 Job Search Intelligence System (MCP + LangGraph Architecture)

## 🎯 Goal

Build an AI-powered system that:

- Fetches AI/ML/Software Engineer jobs in India (onsite/hybrid preferred)
- Aggregates jobs from multiple job APIs via a **Job Source MCP**
- Ranks jobs based on relevance to user profile
- Identifies relevant hiring contacts per company
- Generates personalized outreach messages
- Exports results to Excel daily
- Syncs structured results to Notion via **Notion MCP (manual trigger only)**

This system is designed as a **career intelligence engine**, not a job scraper or job board.

---

## 🚫 Constraints

- No LinkedIn scraping
- No Naukri scraping
- No browser automation for job ingestion
- MCP is ONLY for external system integrations
- Core reasoning, ranking, filtering, and orchestration MUST stay inside LangGraph (not MCP)

---

## 🧠 High-Level Architecture

```text
                 ┌──────────────────────┐
                 │   LangGraph Core     │
                 │ (AI reasoning engine)│
                 └─────────┬────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        │                  │                  │
Job Source MCP      Contact Discovery     Notion MCP
 (data layer)         (logic layer)        (storage layer)
        │                  │                  │
 APIs (Adzuna,     LLM + web reasoning   Notion DB sync
 Remotive, YC,     (NO MCP here)         (manual trigger)
 Wellfound)


```

---

## 🔌 MCP COMPONENTS

### 1. Job Source MCP (DATA LAYER)

* **Purpose:** A unified API layer that fetches jobs from multiple sources and normalizes them into a single schema.


* **Tools:**

* `fetch_jobs(query, location, filters)`

* `get_job_details(job_id)`

* `normalize_job(raw_job)`



* **Data Sources:**

* Adzuna (India-focused jobs)


* Remotive (remote tech jobs)


* Wellfound (startup/AI jobs)


* Y Combinator jobs (startup listings)




* **Output Schema:**


```json
  {
    "title": "",
    "company": "",
    "description": "",
    "location": "",
    "url": "",
    "source": "",
    "date_posted": ""
  }

```

### 2. Notion MCP (STORAGE LAYER)

* **Purpose:** Persist job pipeline state into Notion only when manually triggered.


* **Tools:**

* `create_job_entry(job)`

* `update_job_status(job_id, status)`

* `bulk_sync_jobs(job_list)`

* `log_outreach(job_id, message, contact)`



* **Notion Structure (Jobs Database):**

* New


* Reviewed


* Contacted


* Replied


* Rejected





---

## 🧠 LANGGRAPH CORE SYSTEM (NO MCP HERE)

### 1. Job Ingestion Node

* Calls Job Source MCP.


* Fetches jobs for:


* AI Engineer


* ML Engineer


* LLM Engineer





### 2. Filtering Node

* **Filters:**

* Location must be India / onsite / hybrid India.


* Allowed roles: AI Engineer, ML Engineer, LLM Engineer, Backend (AI-heavy).




* **Removes:**

* HR, Sales, Analyst roles, and irrelevant jobs.





### 3. Deduplication Node

* Remove duplicates across sources.


* **Key:** `company` + `job_title`.



### 4. Ranking Node (LLM-based)

* **Score jobs (0–100):**

* AI/LLM relevance.


* Skill match (LangGraph, RAG, MCP, Python).


* Startup vs enterprise fit.


* Alignment with user profile.




* **Output:**


```json
  {
    "job_id": "",
    "score": 0-100,
    "reason": ""
  }

```

### 5. Contact Discovery Node (NO MCP)

* **Find relevant people per company:**

* Recruiters


* Engineering Managers


* Founders (startups)




* **Output:**


```json
  {
    "company": "",
    "people": [
      {
        "name": "",
        "role": "",
        "profile_url": ""
      }
    ]
  }

```

### 6. Message Generation Node

* **Generate personalized outreach messages:**

> Hi {name},
> I came across your AI Engineer role at {company}.
> Based on my experience in LLMs, RAG pipelines, and agentic systems, this role strongly aligns with my work.
> Would love to connect and learn more.



### 7. Excel Export Node

* **Final output columns:**

* Company


* Role


* Source


* URL


* Score


* Contacts


* Message





---

## ⏱ EXECUTION FLOW

```text
START
  │
  ▼
Fetch Jobs (Job Source MCP)
  │
  ▼
Filter (India + AI roles)
  │
  ▼
Deduplicate
  │
  ▼
Rank (LLM scoring)
  │
  ▼
Select Top 20–30 jobs
  │
  ▼
Find Contacts
  │
  ▼
Generate Messages
  │
  ▼
Export Excel
  │
  ▼
(Manual trigger) Sync to Notion MCP
  │
  ▼
END

```

---

## 🧠 DESIGN PRINCIPLES

* **MCP usage rules:** MCP is ONLY for external systems.


* *Job Source MCP* = ingestion abstraction layer


* *Notion MCP* = persistence layer




* **LangGraph handles:** Orchestration, reasoning, ranking, decision-making, and workflow execution.



---

## 🔧 TECH STACK

* **Language:** Python


* **Orchestration:** LangGraph


* **LLM Integration:** Claude / OpenAI API


* **Data Processing & Export:** Pandas (Excel export)


* **State Tracking:** Postgres (optional)


* **MCP servers:** Job Source MCP, Notion MCP



---

## 🚀 FINAL SYSTEM SUMMARY

This is **NOT** a scraper or job board.

It is a **Career Intelligence System** that transforms raw job listings into ranked, actionable opportunities with personalized outreach and structured tracking.

```

```