import json
import os
from typing import Dict, Any
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from app.services.llm import get_agent_llm

# LLM is lazily initialized to ensure env vars are loaded before first use
_core_llm = None

def _get_llm():
    global _core_llm
    if _core_llm is None:
        _core_llm = get_agent_llm()
    return _core_llm

UI_GENERATION_PROMPT = """
You are the AG-UI (AI-Generated UI) system.
Based on the provided data and context, you must generate a JSON object representing the UI component to be rendered on the frontend.

IMPORTANT AG-UI RENDERING CORRECTION:
The frontend should NOT display raw JSON or simple data cards.
AG-UI JSON is only the instruction layer.
React must convert the AG-UI schema into real interactive components.

You are restricted to the following UI Component types:
- table
- form
- calendar
- dashboard_card
- employee_profile
- document_preview

Return ONLY a valid JSON object. Do not include markdown blocks like ```json ... ```. 
Ensure the JSON is perfectly parseable.

Context Data from MCP or Agent:
{context_data}

Rules for generation based on Context:
1. If the action is candidate deletion (e.g., delete_candidate) and mcp_results contains success, output:
{{
  "type": "dashboard_card",
  "title": "Candidate Deleted",
  "status": "success",
  "message": "Candidate has been successfully removed from the candidate database."
}}
2. If the action is scheduling an interview (e.g., create_interview) and mcp_results contains success, output:
{{
  "type": "dashboard_card",
  "title": "Interview Scheduled",
  "status": "success",
  "data": {{
    "Candidate": "Candidate Name",
    "Time": "Interview Date and Time",
    "Meeting Link": "Google Meet Link",
    "Status": "Confirmed"
  }}
}}
3. If the action is converting a candidate to an employee (e.g., convert_to_employee) and mcp_results contains success, extract the employee details from the mcp_results data field and output:
{{
  "type": "employee_profile",
  "title": "Employee Profile Created",
  "employee": {{
    "name": "<name from mcp_results data>",
    "email": "<email from mcp_results data>",
    "department": "<department from mcp_results data>",
    "position": "<position from mcp_results data>",
    "status": "Active"
  }}
}}
4. If the action is document generation (e.g., generate_document) and mcp_results contains success, output:
{{
  "type": "document_preview",
  "title": "Offer Letter - Candidate Name",
  "candidate_name": "Candidate Name",
  "candidate_role": "Backend Engineer",
  "candidate_email": "candidate@email.com",
  "generated_date": "July 5, 2026",
  "content": "Full offer text...",
  "url": "https://docs.google.com/document/d/..."
}}
5. For listing candidates (e.g. action `get_candidates`) or listing employees, output type "table" with proper columns (including an "actions" column) and contextual table-level/workspace-level actions in the "actions" array (e.g. "+ Add"). Each row must contain an "actions" key with an array of action objects for that row (e.g., Edit, Delete, Update Status).
6. If the action is a dashboard summary or metrics request (e.g. get_dashboard_metrics), output a "dashboard_card" populated with the returned data. It MUST include a "metrics" array. Example:
{{
  "type": "dashboard_card",
  "title": "Candidates Dashboard",
  "metrics": [
    {{"label": "Total Candidates", "value": 150}},
    {{"label": "Applied", "value": 50, "trend": "+5"}},
    {{"label": "Interviewing", "value": 20, "trend": "+2"}}
  ],
  "recent_activity": [
    {{"description": "New candidate applied", "timestamp": "2 mins ago"}}
  ],
  "actions": ["Refresh"]
}}
7. IN-PLACE CALENDAR REFRESH PRIORITY: If the action is fetching calendar events (e.g., get_events) or if `get_events` is anywhere in `mcp_results` with success, YOU MUST PRIORITIZE THIS and output the calendar layout. Ignore rule 2. Output:
{{
  "type": "calendar",
  "title": "Upcoming Events",
  "events": [ array of events from data ]
}}
8. If intent is CREATE_EVENT or UPDATE_EVENT and mcp_results has no success data, output a form with fields (title, start_time, attendees) and submit_action 'create_event' (or update_event). For UPDATE_EVENT, include a hidden "event_id" field.
9. If the action or intent involves creating or editing a candidate (e.g. 'create_candidate', 'update_candidate', 'edit_candidate'):
   - If mcp_results contains a success status, output a "dashboard_card" with a success message confirming the update.
   - If mcp_results DOES NOT contain a success status (or has an error), YOU MUST output a "form". The form should include fields (name, email, phone, role, experience) and submit_action 'create_candidate' (or 'update_candidate'). For editing, include a hidden "id" field populated with the candidate's ID.

Generate the appropriate JSON:
"""

async def generate_ui(context_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a UI JSON structure based on the provided context data.
    """
    # ── PROGRAMMATIC INTENT/MCP DATA INFERENCE ROUTING (Fast, deterministic & error-free) ──
    intent = context_data.get("intent", "").lower()
    mcp_results = context_data.get("mcp_results", [])
    
    successful_results = []
    if isinstance(mcp_results, list):
        for r in mcp_results:
            if isinstance(r, dict) and r.get("result", {}).get("status") == "success":
                successful_results.append(r)

    # Helper: Check if result contains employee data or candidate data
    get_emp_res = next((r for r in successful_results if r.get("action") == "get_employees"), None)
    if intent == "view_employees" or get_emp_res:
        data = get_emp_res.get("result", {}).get("data", []) if get_emp_res else []
        if not data:
            # Scan successful postgres results for any list of employee records
            for r in successful_results:
                candidate_data = r.get("result", {}).get("data")
                if isinstance(candidate_data, list) and candidate_data:
                    sample = candidate_data[0]
                    if "department" in sample or "position" in sample:
                        data = candidate_data
                        break
        
        rows = []
        for emp in data:
            rows.append({
                "Name": emp.get("name") or "N/A",
                "Email": emp.get("email") or "N/A",
                "Role": emp.get("position") or emp.get("role") or "Employee",
                "Department": emp.get("department") or "Engineering",
                "Experience": emp.get("experience") or "N/A",
                "Status": "Active",
                "id": emp.get("id"),
                "actions": [
                    {
                        "label": "View Profile",
                        "event": "view_employee"
                    }
                ]
            })
        return {
            "type": "table",
            "title": "Employee Directory",
            "columns": ["Name", "Email", "Role", "Department", "Experience", "Status", "actions"],
            "data": rows
        }

    # Helper: Check candidate convert profile
    convert_res = next((r for r in successful_results if r.get("action") == "convert_to_employee" or (r.get("action") == "update_candidate" and r.get("result", {}).get("data", {}).get("status") == "employee")), None)
    if convert_res:
        emp_data = convert_res.get("result", {}).get("data", {})
        if not emp_data:
            emp_data = convert_res.get("result", {})
        return {
            "type": "employee_profile",
            "title": "Employee Profile Created",
            "employee": {
                "name": emp_data.get("name") or "Employee",
                "email": emp_data.get("email") or "",
                "department": emp_data.get("department") or "Engineering",
                "position": emp_data.get("position") or "Engineer",
                "status": "Active"
            }
        }

    # Helper: Check candidate delete
    delete_res = next((r for r in successful_results if r.get("action") == "delete_candidate"), None)
    if delete_res:
        return {
            "type": "dashboard_card",
            "title": "Candidate Deleted",
            "status": "success",
            "message": "Candidate has been successfully removed from the candidate database."
        }

    # Helper: Check calendar events
    get_events_res = next((r for r in successful_results if r.get("action") == "get_events" or r.get("server") == "calendar"), None)
    if get_events_res:
        events = get_events_res.get("result", {}).get("data", []) if get_events_res else []
        if not isinstance(events, list):
            events = []
        return {
            "type": "calendar",
            "title": "Upcoming Events",
            "events": events
        }

    # Helper: Check document generation
    doc_res = next((r for r in successful_results if r.get("action") in ["generate_document", "create_document"] or r.get("server") == "docs"), None)
    if doc_res:
        doc_data = doc_res.get("result", {}).get("data", {}) or doc_res.get("result", {})
        candidate_name = context_data.get("selected_candidate") or doc_data.get("candidate_name") or "Candidate"
        return {
            "type": "document_preview",
            "title": f"Offer Letter - {candidate_name}",
            "candidate_name": candidate_name,
            "candidate_role": doc_data.get("candidate_role") or "Backend Engineer",
            "candidate_email": doc_data.get("candidate_email") or "candidate@email.com",
            "generated_date": "July 5, 2026",
            "content": doc_data.get("content") or "Full offer text...",
            "url": doc_data.get("url") or "https://docs.google.com"
        }

    # Helper: Check candidate listing
    get_cand_res = next((r for r in successful_results if r.get("action") == "get_candidates"), None)
    if get_cand_res or intent == "view_candidates" or intent == "list_candidates":
        data = get_cand_res.get("result", {}).get("data", []) if get_cand_res else []
        if not data:
            # Scan successful postgres results for list of candidate records
            for r in successful_results:
                candidate_data = r.get("result", {}).get("data")
                if isinstance(candidate_data, list) and candidate_data:
                    sample = candidate_data[0]
                    if "department" not in sample and "position" not in sample:
                        data = candidate_data
                        break
        
        rows = []
        for c in data:
            rows.append({
                "Name": c.get("name") or "N/A",
                "Email": c.get("email") or "N/A",
                "Role": c.get("role") or "Generalist",
                "Experience": f"{c.get('experience', 0)} years" if c.get('experience') is not None else "N/A",
                "Status": c.get("status") or "applied",
                "id": c.get("id"),
                "actions": [
                    {"label": "View", "event": "view_candidate", "type": "default"},
                    {"label": "Offer", "event": "generate_offer", "type": "default"},
                    {"label": "Schedule", "event": "schedule_interview", "type": "default"},
                    {"label": "Hire", "event": "convert_employee", "type": "primary"},
                    {"label": "Delete", "event": "delete_candidate", "type": "danger"}
                ]
            })
        return {
            "type": "table",
            "title": "Candidates Pipeline",
            "columns": ["Name", "Email", "Role", "Experience", "Status", "actions"],
            "data": rows
        }

    # Fallback to general list inference
    if successful_results:
        first_db_res = next((r for r in successful_results if r.get("server") == "postgres" and isinstance(r.get("result", {}).get("data"), list)), None)
        if first_db_res:
            data = first_db_res.get("result", {}).get("data", [])
            if data:
                sample = data[0]
                if "department" in sample or "position" in sample:
                    # Render employee directory
                    rows = []
                    for emp in data:
                        rows.append({
                            "Name": emp.get("name") or "N/A",
                            "Email": emp.get("email") or "N/A",
                            "Role": emp.get("position") or emp.get("role") or "Employee",
                            "Department": emp.get("department") or "Engineering",
                            "Experience": emp.get("experience") or "N/A",
                            "Status": "Active",
                            "id": emp.get("id"),
                            "actions": [
                                {
                                    "label": "View Profile",
                                    "event": "view_employee"
                                }
                            ]
                        })
                    return {
                        "type": "table",
                        "title": "Employee Directory",
                        "columns": ["Name", "Email", "Role", "Department", "Experience", "Status", "actions"],
                        "data": rows
                    }
                else:
                    # Render candidate directory
                    rows = []
                    for c in data:
                        rows.append({
                            "Name": c.get("name") or "N/A",
                            "Email": c.get("email") or "N/A",
                            "Role": c.get("role") or "Generalist",
                            "Experience": f"{c.get('experience', 0)} years" if c.get('experience') is not None else "N/A",
                            "Status": c.get("status") or "applied",
                            "id": c.get("id"),
                            "actions": [
                                {"label": "View", "event": "view_candidate", "type": "default"},
                                {"label": "Offer", "event": "generate_offer", "type": "default"},
                                {"label": "Schedule", "event": "schedule_interview", "type": "default"},
                                {"label": "Hire", "event": "convert_employee", "type": "primary"},
                                {"label": "Delete", "event": "delete_candidate", "type": "danger"}
                            ]
                        })
                    return {
                        "type": "table",
                        "title": "Candidates Pipeline",
                        "columns": ["Name", "Email", "Role", "Experience", "Status", "actions"],
                        "data": rows
                    }

    # ── LLM GENERATION FALLBACK ──
    prompt = PromptTemplate(
        input_variables=["context_data"],
        template=UI_GENERATION_PROMPT
    )
    
    formatted_prompt = prompt.format(context_data=json.dumps(context_data, indent=2))
    
    response = await _get_llm().ainvoke(formatted_prompt)
    
    try:
        raw_content = response.content.strip()
        # Clean up any potential markdown formatting from LLM
        if raw_content.startswith("```json"):
            raw_content = raw_content[7:]
        if raw_content.startswith("```"):
            raw_content = raw_content[3:]
        if raw_content.endswith("```"):
            raw_content = raw_content[:-3]
            
        ui_json = json.loads(raw_content.strip())
        return ui_json
    except Exception as e:
        # Fallback UI if parsing fails
        return {
            "type": "dashboard_card",
            "title": "Error generating UI",
            "content": f"Failed to parse UI JSON: {str(e)}",
            "raw_data": context_data
        }
