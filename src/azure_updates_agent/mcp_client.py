""" Client for the Microsoft Release Communication MCP Server
All tool arguments are built by typed functions in this module. Raw dicts must never be passed to call_tool
directly - the server silently ignores unknown argument names ( verified 2026-07-10). 
"""
from __future__ import annotations
import logging
from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from tenacity import retry, stop_after_attempt, wait_exponential
import json
from azure_updates_agent.models import AzureUpdate, UpdatesPage

logger=logging.getLogger(__name__)

PAGE_SIZE=50 #fixed by the server; skip advances in this stride
MAX_PAGES=20 # safety valve : never fetch more than 1000 records.
MRC_URL = "https://www.microsoft.com/releasecommunications/mcp"

class MrcClientError(Exception):
    """ Raised when the MRC server returns an unusable response"""


def _odata_quote(value:str)->str:
    """Escape a string literal for use inside an 0Data filter.
    0Data escapes a single quote by doubling it: O'Brien ->O' ' Brien/
    Never Interpolate user/config text into a filter wihtout this.
    """
    return value.replace("'","''")

def build_product_filter(
        products:list[str],
        modified_since:str |None=None,
)->str:
    """Build an OData filter scoping resutls to watched products.
    Products are OR-ed together; the optional modified-since bound is AND-ed so each run fethces only 
    changed since the last run(ISO 8601, e.g. '2026-07-03T00:00:00Z')."""

    if not products:
        raise ValueError('watchlist must contain atleast one product')
    
    product_clauses=" or ".join(f"products/any(p: p eq '{_odata_quote(p)}')" for p in products
    )
    filter_expr=f"({product_clauses})"

    if modified_since is not None:
        filter_expr+=f" and modified ge {modified_since}"
    return filter_expr
@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)

async def _call_tool_once(
    session: ClientSession, name: str, arguments: dict
) -> UpdatesPage:
    """One tool call, parsed and validated. Retried on transient failure."""
    result = await session.call_tool(name, arguments)
    if result.isError:
        raise MrcClientError(f"{name} returned an error: {result.content}")
    for block in result.content:
        if block.type == "text":
            return UpdatesPage.model_validate_json(block.text)
    raise MrcClientError(f"{name} returned no text content block")
async def fetch_updates(filter_expr: str) -> list[AzureUpdate]:
    """Fetch ALL updates matching the filter, following pagination.

    Every returned object is a validated, frozen AzureUpdate parsed
    directly from server output — the only data path into the system.
    """
    updates: list[AzureUpdate] = []
    async with streamablehttp_client(MRC_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            skip = 0
            for page_num in range(MAX_PAGES):
                page = await _call_tool_once(
                    session,
                    "get_recent_azure_updates",
                    {"filter": filter_expr, "skip": skip},
                )
                updates.extend(page.items)
                logger.info(
                    "page %d: got %d of %d total (has_more=%s)",
                    page_num, page.returned_count, page.total_count, page.has_more,
                )
                if not page.has_more:
                    break
                skip += PAGE_SIZE
            else:
                logger.warning(
                    "stopped at MAX_PAGES=%d with has_more still true", MAX_PAGES
                )
    return updates
async def fetch_product_taxonomy() -> set[str]:
    """Fetch the live set of product names via facets.

    Facet shape (verified 2026-07-10): a list of groups, each
    {"name": ..., "values": [{"value": ..., "count": ...}]};
    the group named "Product" holds the flat product list.
    """
    async with streamablehttp_client(MRC_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool(
                "get_recent_azure_updates", {"include_facets": True}
            )
            if result.isError:
                raise MrcClientError(f"facet fetch failed: {result.content}")
            for block in result.content:
                if block.type == "text":
                    payload = json.loads(block.text)
                    for group in payload.get("facets", []):
                        if group.get("name") == "Product":
                            return {v["value"] for v in group["values"]}
    raise MrcClientError("no Product facet group in response")