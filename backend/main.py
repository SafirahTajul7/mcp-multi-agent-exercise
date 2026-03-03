import asyncio
import os
from dotenv import load_dotenv

#--- Framework & AI Imports ---
from langchain.agents import create_agent
from langchain_google_genai import ChatGoogleGenerativeAI
from tenacity import retry, stop_after_attempt, wait_exponential

#--- MCP Client & Tool Imports ---
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_mcp_adapters.tools import load_mcp_tools

#Load environment variables from .env file
load_dotenv()

async def main():
    """
    Main execution pipeline for a multi-server MCP Agent.
    Demonstrates parallel tool loading, resilient execution and multimodal response parsing.
    """

    #________________________________________________________
    # 1: ENVIRONMENT & PATH SETUP
    #________________________________________________________
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY not found in environment variables.")
        return
    
    #Path to local MCP server script
    RANDOM_NUMBER_SCRIPT = os.path.join(os.getcwd(), "server", "stdio", "random_number.py")


    #________________________________________________________
    # 2: MCP CLIENT CONFIGURATION
    #________________________________________________________
    client = MultiServerMCPClient({
        "random_number": {
            "command": "python",
            "args": [RANDOM_NUMBER_SCRIPT],
            "transport": "stdio"
        },
        "roll_dice": {
            "url": "http://localhost:8000/mcp",
            "transport": "streamable_http"
        },
    })


    #________________________________________________________
    # 3: LLM INITIALIZATION
    #Optimized for Gemini 2.5 flash with deterministic temperature
    #________________________________________________________
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.0,
        google_api_key=api_key
    )

    print("Connecting to MCP servers...")

    #________________________________________________________
    # 4: SESSION MANAGEMENT & CONCURRENT TOOL LOADING
    #Using 'async with' ensures sessions are properly closed after execution
    #________________________________________________________
    try:
        async with client.session("random_number") as rn_session, \
                    client.session("roll_dice") as rd_session:
    
            print("Fetching tool schemas in parallel...")

            rn_task = load_mcp_tools(rn_session)
            rd_task = load_mcp_tools(rd_session)

            rn_tools, rd_tools = await asyncio.gather(rn_task, rd_task)
            all_tools = rn_tools + rd_tools 

            print(f"Connected! Loaded {len(all_tools)} tools.")
            for t in all_tools:
                print(f" - Ready: {t.name}")  

            #________________________________________________________
            #5. AGENT DEFINITION
            #Configures the reasoning engine and system contraints.
            #________________________________________________________
            SYSTEM_INSTRUCTIONS = """
                ROLE: Reasoning Assistant with MCP Tool Access.
                CONSTRAINTS:
                1. Analyze intent before tool selection.
                2. Final output must be samitized: Strip internal metadata and JSON.
                3. Provide natural language synthesis of tool results.
            """

            #Returns a compiled state machine that can be invoked with a query
            agent_executor = create_agent(
                llm,
                tools=all_tools,
                system_prompt=SYSTEM_INSTRUCTIONS,
            )

            #________________________________________________________
            #6. RESILIENT LAYER
            #Handles transient network errors or rate limits (Exponential Backoff)
            #________________________________________________________
            @retry(
                stop=stop_after_attempt(3), 
                wait=wait_exponential(multiplier=1, min=2, max=10),
                before_sleep=lambda retry_state: print(f"  Retrying... (attempt {retry_state.attempt_number + 1})")
            )
            async def execute_with_retry(question):
                return await agent_executor.ainvoke({"messages": [("user", question)]})
            
            #________________________________________________________
            #7. Execution & RESPONSE PARSING
            #Handles complex List-based content blocks common in 2026 models.
            #________________________________________________________
            try:
                user_query = "Roll 2 dice for me until you get 6 for both, then let me know how many times."
                print(f"\nUser: {user_query}\n Thinking...")

                result = await execute_with_retry(user_query)

                print("\n" + "="* 50)
                print("Final Response:")
                print("="* 50)

                #Extract content from the last message in the graph state
                final_content = result["messages"][-1].content

                #Handle mutlimodal/segmented content blocks vs raw strings
                if isinstance(final_content, list):
                    text_output = " ".join([block['text'] for block in final_content if 'text' in block])
                    print(text_output)
                else:
                    print(final_content)
                print("="*50)

            except Exception as e:
                # Unwrap RetryError to show actual Gemini error
                actual = e
                if hasattr(e, 'last_attempt') and e.last_attempt.failed:
                    try:
                        e.last_attempt.result()
                    except Exception as inner:
                        actual = inner
                print(f"Agent Runtime Error: {type(actual).__name__}: {actual}")

    except Exception as e:
        print(f"Critical Connection/Session Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
