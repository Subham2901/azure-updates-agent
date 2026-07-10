"""Isolate which filter clause matches nothing, and discover real product names."""

import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

from azure_updates_agent.mcp_client import MRC_URL


async def probe(session: ClientSession, label: str, arguments: dict) -> dict:
    result = await session.call_tool("get_recent_azure_updates", arguments)
    payload = json.loads(result.content[0].text)
    print(f"{label}: totalCount={payload['totalCount']}")
    return payload


async def main() -> None:
    async with streamablehttp_client(MRC_URL) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Hypothesis A: product name is wrong
            await probe(session, "product only",
                {"filter": "products/any(p: p eq 'Azure Kubernetes Service')"})

            # Hypothesis B: date clause is wrong
            await probe(session, "date only",
                {"filter": "modified ge 2026-06-01T00:00:00Z"})

            # Ground truth: what product names actually exist?
            payload = await probe(session, "facets", {"include_facets": True})
            facets = payload.get("facets")
            print("\nfacets type:", type(facets).__name__)
            print(json.dumps(facets, indent=2)[:1500])

            # find kubernetes entries regardless of exact shape
            kube = [f for f in facets if "kube" in json.dumps(f).lower()]
            print("\nKubernetes-related facet entries:")
            print(json.dumps(kube, indent=2))
if __name__ == "__main__":
    asyncio.run(main())