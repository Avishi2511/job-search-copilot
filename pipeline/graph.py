from langgraph.graph import StateGraph, END

from pipeline.state import PipelineState
from pipeline.nodes.ingest import ingest_node
from pipeline.nodes.filter import filter_node
from pipeline.nodes.dedup import dedup_node
from pipeline.nodes.contact_discovery import contact_discovery_node
from pipeline.nodes.message_generation import message_generation_node
from pipeline.nodes.excel_export import excel_export_node


def build_graph() -> StateGraph:
    builder = StateGraph(PipelineState)

    builder.add_node("ingest", ingest_node)
    builder.add_node("filter", filter_node)
    builder.add_node("dedup", dedup_node)
    builder.add_node("contact_discovery", contact_discovery_node)
    builder.add_node("message_generation", message_generation_node)
    builder.add_node("excel_export", excel_export_node)

    builder.set_entry_point("ingest")
    builder.add_edge("ingest", "filter")
    builder.add_edge("filter", "dedup")
    builder.add_edge("dedup", "contact_discovery")
    builder.add_edge("contact_discovery", "message_generation")
    builder.add_edge("message_generation", "excel_export")
    builder.add_edge("excel_export", END)

    return builder.compile()
