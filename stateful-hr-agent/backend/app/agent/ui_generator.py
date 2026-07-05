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
5. For listing candidates or employees, output type "table" with proper columns (including an "actions" column) and contextual table-level/workspace-level actions in the "actions" array (e.g. "+ Add Candidate", "Generate Report", "Refresh"). Each row must contain an "actions" key with an array of action objects for that row (e.g., View Profile, Schedule Interview, Generate Offer, Convert Employee, Delete for candidates; and View Profile, Update Details, Documents for employees).
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

Generate the appropriate JSON:
"""

async def generate_ui(context_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a UI JSON structure based on the provided context data.
    """
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
