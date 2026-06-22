"""
CLI entry point for the Job Search Copilot.

Usage:
  python main.py run          # full pipeline: fetch → filter → dedup → contacts → messages → export
  python main.py sync-notion  # manual Notion sync of last run's results
  python main.py setup-notion # one-time: create the Notion database structure
"""

import argparse
import asyncio
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

LAST_RUN_PATH = Path("output/last_run.json")


async def run_pipeline():
    from pipeline.graph import build_graph

    graph = build_graph()
    initial_state = {
        "raw_jobs": [],
        "filtered_jobs": [],
        "new_jobs": [],
        "jobs_with_contacts": [],
        "final_jobs": [],
    }

    print("Starting job search pipeline...\n")
    result = await graph.ainvoke(initial_state)

    # Persist final jobs so sync-notion can read them without re-running the pipeline
    LAST_RUN_PATH.parent.mkdir(exist_ok=True)
    with open(LAST_RUN_PATH, "w", encoding="utf-8") as f:
        json.dump(result["final_jobs"], f, indent=2, ensure_ascii=False)

    from datetime import date
    output_path = f"output/jobs_{date.today().isoformat()}.xlsx"
    print(f"\nPipeline complete.")
    print(f"  Raw jobs fetched : {len(result['raw_jobs'])}")
    print(f"  After filtering  : {len(result['filtered_jobs'])}")
    print(f"  New (not seen)   : {len(result['new_jobs'])}")
    print(f"  Excel exported   : {output_path}")
    print(f"  Last run saved   : {LAST_RUN_PATH}")
    print(f"\nTo sync to Notion: python main.py sync-notion")
    return result


async def sync_notion():
    if not LAST_RUN_PATH.exists():
        print("No last run found. Run the pipeline first: python main.py run")
        sys.exit(1)

    with open(LAST_RUN_PATH, encoding="utf-8") as f:
        jobs = json.load(f)

    if not jobs:
        print("Last run produced no jobs to sync.")
        sys.exit(0)

    print(f"Syncing {len(jobs)} jobs to Notion...")

    import os
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_servers.notion.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("bulk_sync_to_notion", {"jobs": jobs})
            summary = json.loads(result.content[0].text)

    print(f"\nNotion sync complete.")
    print(f"  Created : {summary['created']}")
    print(f"  Failed  : {summary['failed']}")


async def setup_notion():
    parent_page_id = input("Paste your Notion parent page ID: ").strip()
    if not parent_page_id:
        print("No page ID provided.")
        sys.exit(1)

    import os
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_servers.notion.server"],
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "setup_notion_database", {"parent_page_id": parent_page_id}
            )
            print(result.content[0].text)


def main():
    parser = argparse.ArgumentParser(description="Job Search Copilot")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("run", help="Run the full job search pipeline")
    subparsers.add_parser("sync-notion", help="Manually sync last results to Notion")
    subparsers.add_parser("setup-notion", help="One-time: create the Notion database structure")

    args = parser.parse_args()

    if args.command == "run":
        asyncio.run(run_pipeline())
    elif args.command == "sync-notion":
        asyncio.run(sync_notion())
    elif args.command == "setup-notion":
        asyncio.run(setup_notion())
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
