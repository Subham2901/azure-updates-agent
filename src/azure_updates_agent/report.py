"""Render a Delta into Markdown via Jinja2.

Grounding guarantee: this module contains no free text about updates.
The template interpolates fields of validated, frozen models only —
there is no code path through which invented content can enter.
"""

from __future__ import annotations

from datetime import datetime, timezone

from jinja2 import Environment, PackageLoader, StrictUndefined

from azure_updates_agent.state import Delta

_env = Environment(
    loader=PackageLoader("azure_updates_agent", "templates"),
    undefined=StrictUndefined,   # misspelled field -> loud failure, never blank
    autoescape=False,            # output is Markdown, not HTML (see module docs)
    trim_blocks=True,
    lstrip_blocks=True,
)
def _human_date(dt: object) -> str:
    """Render datetimes as YYYY-MM-DD; pass anything else through."""
    return dt.strftime("%Y-%m-%d") if isinstance(dt, datetime) else str(dt)


_env.filters["human_date"] = _human_date

def render_report(delta: Delta, products: list[str], since: str) -> str:
    template = _env.get_template("report.md.j2")
    return template.render(
        delta=delta,
        products=products,
        since=since,
        generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )