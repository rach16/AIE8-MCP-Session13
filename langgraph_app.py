"""
LangGraph Application with MCP Integration
Demonstrates how LangGraph can work with MCP tools.
"""

import asyncio
import os
from typing import Annotated, TypedDict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI

load_dotenv()

class GraphState(TypedDict):
    messages: Annotated[list, "The messages in the conversation"]
    user_intent: str

class MCPToolRunner:
    """Calls actual MCP server tools"""
    
    async def call_tool(self, tool_name: str, **kwargs) -> str:
        """Call actual MCP server tools"""
        try:
            # Import the actual tool functions directly
            if tool_name == "web_search":
                from server import web_search
                return web_search(**kwargs)
            elif tool_name == "roll_dice":
                from server import roll_dice
                return roll_dice(**kwargs)
            elif tool_name == "get_marketing_news":
                from server import get_marketing_news
                return get_marketing_news(**kwargs)
            elif tool_name == "get_company_news":
                from server import get_company_news
                return get_company_news(**kwargs)
            else:
                return f"❌ Tool {tool_name} not found"
                
        except Exception as e:
            return f"❌ Error calling MCP tool {tool_name}: {str(e)}"

def classify_user_intent(state: GraphState) -> GraphState:
    """Classify what the user wants to do based on their message"""
    messages = state["messages"]
    last_message = messages[-1].content.lower()
    
    # Simple intent classification
    if any(word in last_message for word in ["news", "marketing", "company", "business"]):
        intent = "news"
    elif any(word in last_message for word in ["dice", "roll", "game", "random"]):
        intent = "dice"
    elif any(word in last_message for word in ["search", "web", "look up", "find"]):
        intent = "search"
    else:
        intent = "general"
    
    return {**state, "user_intent": intent}

def create_workflow():
    """Create the LangGraph workflow"""
    
    # Create the LLM
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0.1,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Create MCP tool runner
    tool_runner = MCPToolRunner()
    
    def agent(state: GraphState):
        """The main agent that decides what to do"""
        messages = state["messages"]
        user_intent = state.get("user_intent", "general")
        
        # Create a system message based on intent
        system_prompt = f"""
        You are a helpful assistant with access to MCP tools. The user's intent is: {user_intent}
        
        Available MCP tools:
        - web_search(query): Search the web for information
        - roll_dice(notation, num_rolls): Roll dice with custom notation
        - get_marketing_news(company, category, num_articles): Get marketing news
        - get_company_news(company, num_articles): Get company-specific news
        
        Based on the user's message and intent, decide if you need to call a tool or respond directly.
        If you need to call a tool, respond with: TOOL_CALL:tool_name:arg1=value1:arg2=value2
        Otherwise, respond normally.
        """
        
        # Add system message
        full_messages = [{"role": "system", "content": system_prompt}] + messages
        
        # Get response from LLM
        response = llm.invoke(full_messages)
        
        return {"messages": [response]}
    
    def execute_tools(state: GraphState):
        """Execute tools if the agent wants to use them"""
        messages = state["messages"]
        last_message = messages[-1].content
        
        # Check if the message contains a tool call
        if last_message.startswith("TOOL_CALL:"):
            # Parse the tool call
            parts = last_message.split(":")
            tool_name = parts[1]
            
            # Parse arguments
            args = {}
            for part in parts[2:]:
                if "=" in part:
                    key, value = part.split("=", 1)
                    # Convert numeric values
                    if value.isdigit():
                        args[key] = int(value)
                    else:
                        args[key] = value
            
            # Execute the tool
            tool_result = asyncio.run(tool_runner.call_tool(tool_name, **args))
            
            # Create a response with the tool result
            response = f"I used the {tool_name} tool and got this result:\n\n{tool_result}"
            
            return {"messages": [AIMessage(content=response)]}
        else:
            return {"messages": [last_message]}
    
    def should_continue(state: GraphState) -> str:
        """Determine if we should continue or end"""
        messages = state["messages"]
        last_message = messages[-1].content
        
        if last_message.startswith("TOOL_CALL:"):
            return "execute_tools"
        else:
            return END
    
    # Create the graph
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("classify_intent", classify_user_intent)
    workflow.add_node("agent", agent)
    workflow.add_node("execute_tools", execute_tools)
    
    # Add edges
    workflow.add_edge("classify_intent", "agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "execute_tools": "execute_tools",
            END: END
        }
    )
    workflow.add_edge("execute_tools", END)
    
    # Set entry point
    workflow.set_entry_point("classify_intent")
    
    return workflow.compile()

async def test_langgraph():
    """Test the LangGraph workflow"""
    
    print("🤖 LangGraph MCP Test")
    print("=" * 40)
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not found in .env file")
        return
    
    # Create workflow
    app = create_workflow()
    
    # Test cases
    tests = [
        "Search for information about artificial intelligence",
        "Roll 2d6 dice for me", 
        "Get marketing news about ZoomInfo",
        "Find news about Tesla company"
    ]
    
    for i, test in enumerate(tests, 1):
        print(f"\n📝 Test {i}: {test}")
        print("-" * 30)
        
        try:
            state = {
                "messages": [HumanMessage(content=test)],
                "user_intent": "general"
            }
            
            result = await app.ainvoke(state)
            
            # Get AI response
            ai_messages = [msg for msg in result["messages"] if hasattr(msg, 'content') and not isinstance(msg, HumanMessage)]
            if ai_messages:
                print(f"🤖 Response: {ai_messages[-1].content}")
            else:
                print("❌ No response")
                
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(test_langgraph())