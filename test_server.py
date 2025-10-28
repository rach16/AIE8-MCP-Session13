from mcp.client.stdio import stdio_client
import asyncio

async def main():
    # Connect via stdio to a local script
    from mcp.client.stdio import StdioServerParameters
    server_params = StdioServerParameters(command="uv", args=["run", "server.py"])
    async with stdio_client(server_params) as (read, write):
        from mcp.client.session import ClientSession
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            # List available tools
            tools_result = await session.list_tools()
            print(f"Available tools: {[tool.name for tool in tools_result.tools]}")
            
            # Test web search
            print("\n=== Testing Web Search ===")
            result = await session.call_tool("web_search", {"query": "What is the capital of France?"})
            print(f"Web search result: {result.content[0].text[:200]}...")
            
            # Test dice rolling
            print("\n=== Testing Dice Roll ===")
            dice_result = await session.call_tool("roll_dice", {"notation": "2d6", "num_rolls": 2})
            print(f"Dice roll result: {dice_result.content[0].text}")
            
            # Test marketing news (this will fail without a real API key, but we can see the error)
            print("\n=== Testing Marketing News ===")
            try:
                news_result = await session.call_tool("get_marketing_news", {"company": "ZoomInfo", "num_articles": 2})
                print(f"Marketing news result: {news_result.content[0].text}")
            except Exception as e:
                print(f"Marketing news error (expected without real API key): {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())