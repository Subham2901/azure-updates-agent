""" Throw away exploration : what does the MRC MCP server actually return?
Run: uv run python scripts/explore_mcp.py"""

import asyncio
import json
from pathlib import Path

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

MRC_URL = "https://www.microsoft.com/releasecommunications/mcp"
FIXTURES = Path("tests/fixtures")

async def main()->None:
    async with streamablehttp_client(MRC_URL) as (read,write,_):
        async with ClientSession(read,write) as session:
            await session.initialize()

            #1. What tools does the server advertise?
            tools=await session.list_tools()
            print("===TOOLS===")
            for tool in tools.tools:
                print(f"-{tool.name}:{tool.description}")
                if "azure" in tool.name:
                    print(json.dumps(tool.inputSchema,indent=2))
            #2 Call the Azure updates tool, small page
            result = await session.call_tool(
                "get_recent_azure_updates",{"top":5},
            )

            #3. Dump every content block raw to disk
            print("\n=== RAW RESULT===")
            blocks=[]
            for block in result.content:
                data=block.model_dump()
                blocks.append(data)
                print(json.dumps(data,indent=2)[:2000])
            FIXTURES.mkdir(parents=True, exist_ok=True)
            out = FIXTURES/"raw_azure_updates.json"
            out.write_text(json.dumps(blocks,indent=2))
            print(f"\n Saved raw response to {out}")
            
if __name__=="__main__":
    asyncio.run(main())