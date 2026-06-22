import pandas as pd
from datetime import date
from pathlib import Path

from pipeline.state import PipelineState


def _format_contacts(contacts: list[dict]) -> str:
    if not contacts:
        return ""
    lines = []
    for c in contacts:
        name = c.get("name", "")
        role = c.get("role", "")
        url = c.get("profile_url", "")
        line = f"{name} ({role})"
        if url:
            line += f"\n{url}"
        lines.append(line)
    return "\n\n".join(lines)


async def excel_export_node(state: PipelineState) -> dict:
    jobs = state["final_jobs"]

    rows = []
    for job in jobs:
        rows.append({
            "Company": job.get("company", ""),
            "Role": job.get("title", ""),
            "Location": job.get("location", ""),
            "Source": job.get("source", ""),
            "URL": job.get("url", ""),
            "Date Posted": job.get("date_posted", ""),
            "Contacts Found": _format_contacts(job.get("contacts", [])),
            "Outreach Message": job.get("outreach_message", ""),
        })

    df = pd.DataFrame(rows)

    output_dir = Path(__file__).parent.parent.parent / "output"
    output_dir.mkdir(exist_ok=True)
    filename = output_dir / f"jobs_{date.today().isoformat()}.xlsx"

    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Jobs")

        ws = writer.sheets["Jobs"]

        # Column widths
        col_widths = {
            "A": 25,  # Company
            "B": 35,  # Role
            "C": 25,  # Location
            "D": 12,  # Source
            "E": 50,  # URL
            "F": 14,  # Date Posted
            "G": 40,  # Contacts Found
            "H": 70,  # Outreach Message
        }
        for col, width in col_widths.items():
            ws.column_dimensions[col].width = width

        # Wrap text for contacts and message columns
        from openpyxl.styles import Alignment
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                cell.alignment = Alignment(wrap_text=True, vertical="top")

        # Freeze header row
        ws.freeze_panes = "A2"

    print(f"[excel_export] Exported {len(rows)} jobs → {filename}")
    return {}
