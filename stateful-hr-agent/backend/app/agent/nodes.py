import json
import os
import re
from langchain_core.messages import AIMessage
from app.agent.state import AgentState
from app.agent.prompts import (
    INTENT_DETECTION_PROMPT, 
    PLANNING_PROMPT, 
    RESPONSE_PROMPT
)
from app.mcp.client import mcp_client
from app.services.llm import get_agent_llm, get_fast_llm
from app.agent.ui_generator import generate_ui

_core_llm = None
_content_llm = None

def get_core_llm():
    global _core_llm
    if _core_llm is None: _core_llm = get_agent_llm()
    return _core_llm

def get_content_llm():
    global _content_llm
    if _content_llm is None: _content_llm = get_fast_llm()
    return _content_llm

def clean_json_response(content: str) -> str:
    cleaned = content.strip()
    if cleaned.startswith("```json"): cleaned = cleaned[7:]
    if cleaned.startswith("```"): cleaned = cleaned[3:]
    if cleaned.endswith("```"): cleaned = cleaned[:-3]
    return cleaned.strip()

def extract_name_prefix_query(user_message: str):
    """Extract exact one-letter prefix from requests like: 'name starts with p'."""
    if not user_message:
        return None

    msg = user_message.lower()
    patterns = [
        r'\b(?:name|names|candidate|candidates)?\s*(?:that\s+)?starts?\s+with\s+[\"\']?([a-z])[\"\']?\b',
        r'\bstarting\s+with\s+[\"\']?([a-z])[\"\']?\b',
    ]
    for pat in patterns:
        m = re.search(pat, msg)
        if m:
            return m.group(1)
    return None

ACTION_MAP = {
    "update_record": "update_candidate",
    "modify_candidate": "update_candidate",
    "database_update": "update_candidate",
    "edit_candidate": "update_candidate",
    "list_candidates": "get_candidates",
    "view_candidates": "get_candidates",
    "list_employees": "get_employees",
    "view_employees": "get_employees",
    "remove_candidate": "delete_candidate",
    "schedule_interview": "create_event", # will map to create_interview
    "book_meeting": "create_event",
    "list_interviews": "get_events",
    "view_calendar": "get_events",
    "show_calendar": "get_events",
    "fetch_events": "get_events",
    "generate_offer": "generate_document",
}

async def input_node(state: AgentState) -> AgentState:
    user_message = state["messages"][-1].content
    print(f"\n[1] INPUT\n{user_message}")
    return state

async def intent_detection(state: AgentState) -> AgentState:
    user_message = state["messages"][-1].content
    prompt = INTENT_DETECTION_PROMPT.format(
        selected_candidate=state.get("selected_candidate", "None"),
        user_message=user_message
    )
    response = await get_core_llm().ainvoke(prompt)
    try:
        raw_json = clean_json_response(response.content)
        data = json.loads(raw_json)
        
        intent = data.get("intent", "UNKNOWN")
        entities = data.get("entities", {})
        print(f"\n[2] INTENT\n{{\n \"intent\":\"{intent}\"\n}}")
        
        return {
            "intent": intent,
            "entities": entities,
            "required_tools": data.get("required_tools", [])
        }
    except Exception as e:
        print(f"\n[2] INTENT\nFAILED: {e}")
        return {"intent": "ERROR", "entities": {}, "required_tools": []}

async def memory_retrieval(state: AgentState) -> AgentState:
    # Resolve pronouns from visible context
    user_message = state["messages"][-1].content.lower()
    entities = state.get("entities", {})
    visible = state.get("visible_context", [])
    
    if "her" in user_message or "him" in user_message or "them" in user_message:
        if visible and len(visible) > 0 and "candidate" not in entities:
            # Just grab the first one for the demo
            entities["candidate"] = visible[0].get("name")
            return {"entities": entities}
            
    return state

def build_calendar_view_plan(entities: dict) -> list:
    params = {}
    candidate_name = (
        entities.get("candidate_name")
        or entities.get("candidate")
        or entities.get("name")
    )
    if candidate_name:
        params["candidate_name"] = candidate_name

    if entities.get("start_date"):
        params["start_date"] = entities.get("start_date")
    if entities.get("end_date"):
        params["end_date"] = entities.get("end_date")

    return [{
        "step": 1,
        "tool": "calendar_mcp",
        "action": "get_events",
        "parameters": params,
    }]


def enforce_plan_guardrails(intent: str, entities: dict, plan: list) -> list:
    # Hard guardrail: calendar viewing intents must never mutate events.
    if intent == "view_interview_calendar":
        return build_calendar_view_plan(entities)
    return plan

async def planning_node(state: AgentState) -> AgentState:
    intent = state.get("intent", "")
    entities = state.get("entities", {})
    required_tools = state.get("required_tools", [])
    
    prompt = PLANNING_PROMPT.format(
        intent=intent,
        entities=json.dumps(entities),
        required_tools=json.dumps(required_tools)
    )
    
    response = await get_core_llm().ainvoke(prompt)
    try:
        raw_json = clean_json_response(response.content)
        plan = json.loads(raw_json)
        if not isinstance(plan, list):
            plan = []
        if intent == "view_employees" or ("employee" in intent.lower() and any(verb in intent.lower() for verb in ["list", "show", "get", "view", "all"])):
            plan = [{"step": 1, "tool": "postgres_mcp", "action": "get_employees", "parameters": {}}]
        plan = enforce_plan_guardrails(intent, entities, plan)
        print(f"\n[3] PLAN\n{json.dumps(plan, indent=1)}")
        return {"plan": plan}
    except Exception as e:
        print(f"\n[3] PLAN\nFAILED: {e}")
        fallback_plan = enforce_plan_guardrails(intent, entities, [])
        return {"plan": fallback_plan}

async def mcp_execution(state: AgentState) -> AgentState:
    plan = state.get("plan", [])
    selected_candidate = state.get("selected_candidate")
    entities = state.get("entities", {})
    visible_context = state.get("visible_context", [])
    intent = state.get("intent", "UNKNOWN")
    user_message = state["messages"][-1].content if state.get("messages") else "N/A"
    
    if "candidate" in entities:
        selected_candidate = entities["candidate"]
        
    print("\n========== MCP EXECUTION ==========")
    print(f"USER REQUEST:\n{user_message}")
    print(f"\nINTENT:\n{intent}")
    print(f"\nRESOLVED ENTITY (Initial):\n{selected_candidate}")
    print(f"\nPLAN GENERATED:\n{json.dumps(plan, indent=2)}")
    
    results = []
    context = {}
    trace_log = f"ðŸ§  GPT-5.1\nIntent: {state.get('intent', 'unknown')}\n\n"
    
    for step in plan:
        tool_raw = step.get("tool", "")
        if tool_raw == "none":
            continue
            
        server = tool_raw.replace("_mcp", "")
        raw_action = step.get("action", "")
        action = ACTION_MAP.get(raw_action, raw_action)
        
        # fix invalid actions mapped by GPT
        if action in ["get_records", "get_candidates"] and "employee" in intent.lower():
            action = "get_employees"
        elif action == "get_records":
            action = "get_candidates"
                
        if server == "calendar" and action in ["create_interview", "schedule_interview"]:
            action = "create_event"
        if server == "calendar" and action in ["list_interviews", "view_calendar", "show_calendar", "fetch_events", "view_interview_calendar"]:
            action = "get_events"
        if server == "postgres" and action == "convert_to_employee":
            action = "update_candidate"
            if not isinstance(step.get("parameters"), dict):
                step["parameters"] = {}
            step["parameters"]["status"] = "employee"

        raw_payload = step.get("parameters", {})
        payload = raw_payload if isinstance(raw_payload, dict) else {}

        # Deterministic guardrail for prompts like: "names starting with p"
        if server == "postgres" and action == "get_candidates":
            forced_prefix = extract_name_prefix_query(user_message)
            if forced_prefix:
                payload["starts_with"] = forced_prefix

        needs_entity = action in ["update_candidate", "delete_candidate", "convert_to_employee", "create_event", "send_email", "generate_document"]
        if needs_entity and "id" not in payload and "candidate_id" not in payload:
            name = payload.get("name") or payload.get("candidate_name") or selected_candidate
            if name:
                print(f"\nEntity resolver:\nSearching candidates table: name={name}")
                lookup = await mcp_client.execute("postgres", "get_candidates", {})
                found = None
                for c in lookup.get("data", []):
                    if name.lower() in str(c.get("name", "")).lower():
                        found = c
                        break
                if found:
                    print(f"Found:\n{{\n id: {found.get('id')}\n name: {found.get('name')}\n email: {found.get('email')}\n}}")
                    trace_log += f"ðŸ” Database MCP\nFound {found.get('name')}\n\n"
                    context["candidate_id"] = found["id"]
                    context["candidate_email"] = found.get("email")
                    context["candidate_name"] = found.get("name")
                    selected_candidate = found.get("name")

        if "candidate_id" not in payload and "candidate_id" in context:
            payload["id"] = context["candidate_id"]
            payload["candidate_id"] = context["candidate_id"]
        if "to" not in payload and "candidate_email" in context:
            payload["to"] = context["candidate_email"]
        if "candidate_name" not in payload and "candidate_name" in context:
            payload["candidate_name"] = context["candidate_name"]

        if server == "gmail" and action == "send_email":
            content_prompt = f"Write a professional HR email regarding an interview for {payload.get('to', selected_candidate)}. Keep it concise."
            res = await get_content_llm().ainvoke(content_prompt)
            payload["body"] = res.content
            
        elif server == "docs" and action == "generate_document":
            candidate_name = payload.get("candidate_name") or selected_candidate or "Candidate"
            content_prompt = f"Write a professional HR Offer Letter for {candidate_name}. Include a warm welcome. Do NOT use brackets or placeholder terms like [Company Name], [Salary], [Location], [Date], [HR Name], [Start Date], etc. Instead, use these actual values: Company: Phantom Technologies, Location: Chennai, HR: HR Manager, Salary: INR 12,0,000 per annum, Position: Backend Engineer, Start Date: Next Monday. Generate the full, complete document text."
            res = await get_content_llm().ainvoke(content_prompt)
            text_content = res.content
            # Post-process replacement in case LLM outputs placeholders anyway
            text_content = text_content.replace("[Company Name]", "Phantom Technologies").replace("[Company]", "Phantom Technologies")
            text_content = text_content.replace("[Location]", "Chennai")
            text_content = text_content.replace("[HR Name]", "HR Manager").replace("[HR Manager]", "HR Manager")
            text_content = text_content.replace("[Salary]", "INR 12,0,000 per annum")
            text_content = text_content.replace("[Date]", "July 5, 2026")
            text_content = text_content.replace("[Position]", "Backend Engineer").replace("[Job Title]", "Backend Engineer")
            payload["content"] = text_content
            
        print(f"\nTOOL:\n{server}_mcp\nACTION:\n{action}\nINPUT PAYLOAD:\n{json.dumps(payload, indent=2)}")
        
        try:
            result = await mcp_client.execute(server, action, payload)
            
            if action in ["get_candidates", "get_employees"] and result.get("status") == "success":
                data = result.get("data", [])
                if data and isinstance(data, list):
                    visible_context = data
                    if len(data) == 1:
                        if action == "get_candidates":
                            context["candidate_id"] = data[0].get("id")
                            context["candidate_email"] = data[0].get("email")
                            context["candidate_name"] = data[0].get("name")
                        else:
                            context["employee_id"] = data[0].get("id")
                            context["employee_email"] = data[0].get("email")
                            context["employee_name"] = data[0].get("name")
                        trace_log += f"ðŸ” Database MCP\nFound {data[0].get('name')}\n\n"
                        
            if server == "calendar" and result.get("status") == "success":
                if action == "get_events":
                    trace_log += f"ðŸ“… Calendar MCP\nRetrieved events\n\n"
                elif action == "cancel_event":
                    trace_log += f"ðŸ“… Calendar MCP\nEvent cancelled\n\n"
                else:
                    trace_log += f"ðŸ“… Calendar MCP\nEvent scheduled/updated\n\n"
            if server == "docs" and result.get("status") == "success":
                trace_log += f"ðŸ“„ Docs MCP\nOffer created\n\n"
            if server == "gmail" and result.get("status") == "success":
                trace_log += f"ðŸ“§ Gmail MCP\nEmail sent\n\n"
            if server == "postgres" and action in ["convert_to_employee", "update_candidate", "delete_candidate", "create_candidate"] and result.get("status") == "success":
                trace_log += f"ðŸ’¾ Postgres MCP\nDatabase updated successfully\n\n"
                    
        except Exception as e:
            result = {"status": "error", "message": str(e)}
            
        print(f"\nRAW MCP RESULT:\n{json.dumps(result, indent=2)}")
        print(f"SUCCESS/FAIL:\n{'SUCCESS' if result.get('status') == 'success' else 'FAIL'}")
            
        results.append({
            "step": step.get("step"),
            "server": server,
            "action": action,
            "result": result
        })
        
    trace_log += "âœ… Complete"
    print("\n===================================\n")
        
    return {
        "mcp_results": results,
        "selected_candidate": selected_candidate,
        "visible_context": visible_context,
        "agent_trace_log": trace_log
    }

async def ag_ui_generation(state: AgentState) -> AgentState:
    mcp_results = state.get("mcp_results", [])
    intent = state.get("intent", "")
    
    context_data = {
        "intent": intent,
        "entities": state.get("entities", {}),
        "plan": state.get("plan", []),
        "mcp_results": mcp_results,
        "selected_candidate": state.get("selected_candidate")
    }
    
    ui_data = await generate_ui(context_data)
    print(f"\n[6] AG-UI GENERATED\ntype:\n{ui_data.get('type')}\n")
    return {"last_ui": ui_data}

async def response_node(state: AgentState) -> AgentState:
    intent = state.get("intent", "UNKNOWN")
    mcp_results = state.get("mcp_results", [])
    selected_candidate = state.get("selected_candidate", "Candidate")
    
    prompt = f"""You are a professional HR assistant.
State what was done based on the intent '{intent}' and these tool results: {json.dumps(mcp_results)}.
Candidate name: {selected_candidate}

Write a single, friendly, short sentence summarizing the action (e.g. "Candidate Priya was deleted successfully" or "Interview scheduled for Rahul and invite email sent").
Do not output any JSON, technical names, database schemas, or technical terms like database, sql, mcp, etc.
Summary:"""
    try:
        res = await get_content_llm().ainvoke(prompt)
        summary = res.content.strip()
    except Exception:
        summary = f"Workflow completed successfully for {selected_candidate}."
        
    return {"messages": [AIMessage(content=summary)]}
