import os
from langchain_openai import AzureChatOpenAI

def get_agent_llm():
    """
    Returns the main reasoning model (e.g., GPT-5.1).
    Used for LangGraph nodes, intent detection, workflow planner,
    MCP router decisions, and AG-UI JSON generation.
    """
    return AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_AGENT_DEPLOYMENT", "gpt-5.1"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
        temperature=0
    )

def get_fast_llm():
    """
    Returns the fast helper model (e.g., GPT-4o-mini).
    Used for email text, candidate summaries, resume summaries,
    and simple generation.
    """
    return AzureChatOpenAI(
        azure_deployment=os.getenv("AZURE_OPENAI_FAST_DEPLOYMENT", "gpt-4o-mini"),
        api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview"),
        temperature=0.7
    )
