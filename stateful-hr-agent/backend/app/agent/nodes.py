import json
import os
from langchain_core.messages import AIMessage
from langchain_openai import AzureChatOpenAI
from app.agent.state import AgentState
from app.agent.prompts import (
    INTENT_DETECTION_PROMPT, 
    PLANNING_PROMPT, 
    TOOL_SELECTION_PROMPT, 
    RESPONSE_PROMPT
)
from app.mcp.client import mcp_client
from app.services.llm import get_agent_llm, get_fast_llm

# Initialize LLMs using the centralized provider
core_llm = get_agent_llm()
content_llm = get_fast_llm()

async def input_node(state: AgentState) -> AgentState:
    # Passthrough
    return state

async def intent_detection(state: AgentState) -> AgentState:
    user_message = state["messages"][-1].content
    prompt = INTENT_DETECTION_PROMPT.format(
        selected_candidate=state.get("selected_candidate"),
        current_workflow=state.get("current_workflow"),
        user_message=user_message
    )
    response = await core_llm.ainvoke(prompt)
    return {"intent": response.content.strip()}

async def memory_retrieval(state: AgentState) -> AgentState:
    # Future integration point for reading ConversationMemory and AgentState from Postgres DB
    return state

async def planning_node(state: AgentState) -> AgentState:
    prompt = PLANNING_PROMPT.format(
        intent=state.get("intent"),
        selected_candidate=state.get("selected_candidate")
    )
    response = await core_llm.ainvoke(prompt)
    return {"plan": response.content.strip()}

async def tool_selection(state: AgentState) -> AgentState:
    prompt = TOOL_SELECTION_PROMPT.format(
        intent=state.get("intent"),
        plan=state.get("plan")
    )
    response = await core_llm.ainvoke(prompt)
    try:
        raw_content = response.content.replace("```json", "").replace("```", "").strip()
        tool_data = json.loads(raw_content)
        return {
            "selected_tool": tool_data.get("server"),
            "tool_payload": tool_data
        }
    except Exception:
        return {"selected_tool": None, "tool_payload": None}

async def mcp_execution(state: AgentState) -> AgentState:
    tool_payload = state.get("tool_payload")
    if not tool_payload:
        return {"mcp_result": {"status": "error", "message": "No tool selected"}}
        
    server = tool_payload.get("server")
    action = tool_payload.get("action")
    payload = tool_payload.get("payload", {})
    
    # State update simulation based on intent & action
    selected_candidate = state.get("selected_candidate")
    if action == "get_candidates" and "name" in payload:
        # User is looking up someone, update state
        selected_candidate = payload["name"]

    # Use GPT-4o-mini (content_llm) dynamically for content tasks
    if server == "gmail" and action == "send_email":
        content_prompt = f"Write a professional HR email regarding an interview for {payload.get('to', selected_candidate)}. Keep it concise."
        res = await content_llm.ainvoke(content_prompt)
        payload["body"] = res.content
        
    elif server == "docs" and action == "generate_document":
        content_prompt = f"Write a professional HR Offer Letter for {payload.get('candidate_name', selected_candidate)}. Include a warm welcome and standard placeholder terms."
        res = await content_llm.ainvoke(content_prompt)
        payload["content"] = res.content
        
    result = await mcp_client.execute(server, action, payload)
    
    return {
        "mcp_result": result,
        "selected_candidate": selected_candidate
    }

from app.agent.ui_generator import generate_ui

async def ag_ui_generation(state: AgentState) -> AgentState:
    mcp_result = state.get("mcp_result", {})
    intent = state.get("intent", "")
    
    # Bundle context data to give the UI Generator enough information
    context_data = {
        "mcp_result": mcp_result,
        "intent": intent,
        "selected_candidate": state.get("selected_candidate")
    }
    
    ui_data = await generate_ui(context_data)
    return {"last_ui": ui_data}

async def response_node(state: AgentState) -> AgentState:
    prompt = RESPONSE_PROMPT.format(
        mcp_result=state.get("mcp_result"),
        last_ui=state.get("last_ui")
    )
    response = await core_llm.ainvoke(prompt)
    return {"messages": [AIMessage(content=response.content)]}
