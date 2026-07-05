INTENT_DETECTION_PROMPT = """
You are the intent detection module of an AI HR Agent.
Analyze the user's latest message and current conversation history.
Determine the primary intent, extract any relevant entities, and determine the required MCP tools to fulfill the intent.

Available MCP tools:
- postgres_mcp: for any database queries, CRUD operations on candidates, employees, interviews.
- calendar_mcp: for scheduling, creating, updating, listing (viewing) events / interviews.
- gmail_mcp: for sending emails or creating drafts.
- docs_mcp: for generating documents like offer letters.

For calendar-related listing requests (e.g. "show interview calendar", "upcoming interviews", "show Rahul interviews"), detect the intent as "view_interview_calendar" and require tool "calendar_mcp".
For employee listing requests (e.g. "show employees", "list employees", "all employees"), detect the intent as "list_employees" and require tool "postgres_mcp".

User Message: {user_message}
Conversation History context:
Selected Candidate: {selected_candidate}

Return ONLY a valid JSON object in the following format:
{{
 "intent": "descriptive_intent_string",
 "entities": {{"key": "value"}},
 "required_tools": ["tool_name_1", "tool_name_2"]
}}
"""

PLANNING_PROMPT = """
You are the planning module of an AI HR Agent.
Based on the intent '{intent}', entities {entities}, and required tools {required_tools}, produce a strict executable plan.

ALLOWED TOOLS AND ACTIONS:
- postgres_mcp: get_candidates, get_employees, create_candidate, update_candidate, delete_candidate, convert_to_employee, get_dashboard_metrics
- calendar_mcp: get_events, create_interview, update_event, cancel_event
- gmail_mcp: send_email, create_draft
- docs_mcp: generate_document, update_document, get_dashboard_metrics

CRITICAL RULES FOR MULTI-STEP WORKFLOWS:
1. ENTITY RESOLUTION FIRST: If the user asks to schedule an interview, generate an offer, convert an employee, or delete a candidate, STEP 1 MUST ALWAYS be `postgres_mcp.get_candidates` with the `name` parameter to find the candidate. Never ask the user for an ID.
2. SCHEDULE INTERVIEW WORKFLOW: Step 1: get_candidates. Step 2: calendar_mcp.create_interview. Step 3: gmail_mcp.send_email.
3. OFFER LETTER WORKFLOW: Step 1: get_candidates. Step 2: docs_mcp.generate_document.
4. CONVERT EMPLOYEE WORKFLOW: Step 1: postgres_mcp.get_candidates to resolve entity. Step 2: postgres_mcp.convert_to_employee with the resolved candidate id.
5. LIST EMPLOYEES WORKFLOW: For intents like 'show employees', 'list employees', 'all employees', use postgres_mcp.get_employees in a single step.
6. CALENDAR VIEW: If the user asks to see the calendar, schedule, or upcoming events, use calendar_mcp.get_events.
7. IN-PLACE CALENDAR REFRESH: If the user explicitly asks to create, update, or cancel a calendar event directly (e.g. from the calendar UI), the plan MUST be a multi-step workflow ending with `calendar_mcp.get_events` as the last step so the UI can refresh in-place.
8. NO EMPTY FORMS: AG-UI forms are fallbacks. If you have enough data to execute the MCP directly, DO IT. Do not return `render_form` unless you are absolutely missing data that cannot be inferred or generated.

Return ONLY a JSON array of steps. Every step MUST have keys: step, tool, action, parameters.

Example:
[
  {{
    "step": 1,
    "tool": "postgres_mcp",
    "action": "get_candidates",
    "parameters": {{"name": "Priya"}}
  }},
  {{
    "step": 2,
    "tool": "docs_mcp",
    "action": "generate_document",
    "parameters": {{}}
  }}
]
"""

AG_UI_PROMPT = """
(This prompt is now handled by ui_generator.py)
"""

RESPONSE_PROMPT = """
Based on the full context, generate a conversational response to the user.
"""
