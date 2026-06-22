"""
CLI entry point for the Job Search Copilot.

Usage:
  python main.py run          # full pipeline: fetch → filter → dedup → contacts → messages → export
  python main.py sync-notion  # manual Notion sync of last run's results (Phase 6)
"""

import argparse
import asyncio
import sys
from dotenv import load_dotenv

load_dotenv()


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

    print(f"\nPipeline complete.")
    print(f"  Raw jobs fetched : {len(result['raw_jobs'])}")
    print(f"  After filtering  : {len(result['filtered_jobs'])}")
    print(f"  New (not seen)   : {len(result['new_jobs'])}")
    return result


def sync_notion():
    # Wired up in Phase 6
    raise NotImplementedError("Notion sync not implemented yet — coming in Phase 6.")


def main():
    parser = argparse.ArgumentParser(description="Job Search Copilot")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("run", help="Run the full job search pipeline")
    subparsers.add_parser("sync-notion", help="Manually sync last results to Notion")

    args = parser.parse_args()

    if args.command == "run":
        asyncio.run(run_pipeline())
    elif args.command == "sync-notion":
        sync_notion()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
