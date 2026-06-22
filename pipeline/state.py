from typing import TypedDict


class PipelineState(TypedDict):
    raw_jobs: list[dict]            # output of ingest node
    filtered_jobs: list[dict]       # output of filter node
    new_jobs: list[dict]            # output of dedup node (novel jobs not seen before)
    jobs_with_contacts: list[dict]  # output of contact discovery node (Phase 4)
    final_jobs: list[dict]          # output of message generation node (Phase 4)
