import sys
import json
import asyncio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from pipeline.config import load_config
from pipeline.state import PipelineState


async def ingest_node(state: PipelineState) -> dict:
    config = load_config()
    queries: list[str] = config["jobs"]["search_queries"]
    max_results: int = config["jobs"]["max_results_per_source"]

    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "mcp_servers.job_source.server"],
    )

    all_jobs: list[dict] = []

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            for query in queries:
                print(f"[ingest] Fetching jobs for query: '{query}'")
                result = await session.call_tool(
                    "get_all_jobs",
                    {
                        "query": query,
                        "location": "India",
                        "max_results_per_source": max_results,
                    },
                )
                jobs = json.loads(result.content[0].text)
                print(f"[ingest]   → {len(jobs)} jobs fetched")
                all_jobs.extend(jobs)

    print(f"[ingest] Total raw jobs collected: {len(all_jobs)}")
    return {"raw_jobs": all_jobs}
