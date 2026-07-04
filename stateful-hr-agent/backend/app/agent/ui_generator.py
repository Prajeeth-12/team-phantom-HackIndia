import json
import os
from typing import Dict, Any
from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import PromptTemplate
from app.services.llm import get_agent_llm

# Initialize Azure LLM using centralized provider
core_llm = get_agent_llm()

UI_GENERATION_PROMPT = """
You are the AG-UI (AI-Generated UI) system.
Based on the provided data and context, you must generate a JSON object representing the UI component to be rendered on the frontend.

You are restricted to the following UI Component types:
- table
- form
- calendar
- dashboard_card
- timeline
- document_preview

Return ONLY a valid JSON object. Do not include markdown blocks like ```json ... ```. 
Ensure the JSON is perfectly parseable.

Context Data from MCP or Agent:
{context_data}

Rules for generation based on Context:
1. If intent is CREATE_CANDIDATE or UPDATE_CANDIDATE and mcp_result has no success data, output a form with fields (name, email, role) and submit_action 'create_candidate' (or update_candidate).
2. If intent is VIEW_CANDIDATES or get_candidates succeeded, output a table. Make sure actions array includes ["edit", "delete", "schedule"].
3. If an action succeeded (like delete or create), output a dashboard_card summarizing the success.

Example Form JSON:
{{
  "type": "form",
  "title": "Add Candidate",
  "fields": [
    {{"name": "name", "type": "text"}},
    {{"name": "email", "type": "email"}},
    {{"name": "role", "type": "text"}}
  ],
  "submit_action": "create_candidate"
}}

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
    
    response = await core_llm.ainvoke(formatted_prompt)
    
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
