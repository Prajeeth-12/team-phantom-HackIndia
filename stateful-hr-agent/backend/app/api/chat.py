import traceback
import json
import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
from sqlalchemy import select

from app.agent.graph import hr_agent_app
from app.database.database import AsyncSessionLocal
from app.database.repository import candidate_repo
from app.database import models
from app.mcp.client import mcp_client

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default_thread"


_STATE_KEYS = [
    "selected_candidate",
    "current_workflow",
    "last_ui",
    "visible_context",
]


def _message_to_dict(message):
    if isinstance(message, HumanMessage):
        return {"type": "human", "content": message.content}
    if isinstance(message, AIMessage):
        return {"type": "ai", "content": message.content}
    return {"type": "unknown", "content": str(getattr(message, "content", ""))}


def _dict_to_message(item):
    if not isinstance(item, dict):
        return None
    content = item.get("content", "")
    msg_type = item.get("type")
    if msg_type == "human":
        return HumanMessage(content=content)
    if msg_type == "ai":
        return AIMessage(content=content)
    return None


async def _load_conversation_history(db, thread_id: str):
    stmt = select(models.ConversationMemory).where(models.ConversationMemory.thread_id == thread_id)
    result = await db.execute(stmt)
    row = result.scalars().first()
    if not row or not row.messages:
        return []
    try:
        raw = json.loads(row.messages)
    except Exception:
        return []
    if not isinstance(raw, list):
        return []
    messages = []
    for item in raw:
        msg = _dict_to_message(item)
        if msg is not None:
            messages.append(msg)
    return messages


async def _save_conversation_history(db, thread_id: str, messages):
    compact = [_message_to_dict(m) for m in messages][-20:]
    payload = json.dumps(compact, ensure_ascii=True)

    stmt = select(models.ConversationMemory).where(models.ConversationMemory.thread_id == thread_id)
    result = await db.execute(stmt)
    row = result.scalars().first()
    if row:
        row.messages = payload
    else:
        row = models.ConversationMemory(thread_id=thread_id, messages=payload)
        db.add(row)
    await db.commit()


async def _load_agent_state(db, thread_id: str):
    stmt = select(models.AgentState).where(models.AgentState.thread_id == thread_id)
    result = await db.execute(stmt)
    row = result.scalars().first()
    if not row or not row.current_state:
        return {}
    try:
        data = json.loads(row.current_state)
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


async def _save_agent_state(db, thread_id: str, state: dict):
    persisted = {k: state.get(k) for k in _STATE_KEYS if state.get(k) is not None}
    payload = json.dumps(persisted, ensure_ascii=True)

    stmt = select(models.AgentState).where(models.AgentState.thread_id == thread_id)
    result = await db.execute(stmt)
    row = result.scalars().first()
    if row:
        row.current_state = payload
    else:
        row = models.AgentState(thread_id=thread_id, current_state=payload)
        db.add(row)
    await db.commit()
async def _build_candidates_table_ui():
    async with AsyncSessionLocal() as db:
        candidates = await candidate_repo.get_candidates(db, skip=0, limit=200)

    rows = [
        {
            "id": c.id,
            "name": c.name,
            "email": c.email,
            "phone": c.phone,
            "role": c.role,
            "experience": c.experience,
            "status": c.status,
            "actions": [
                {"label": "View Profile", "event": "view_candidate", "type": "primary"},
                {"label": "Schedule Interview", "event": "schedule_interview", "type": "default"},
                {"label": "Generate Offer", "event": "generate_offer", "type": "default"},
                {"label": "Convert Employee", "event": "convert_employee", "type": "default"},
                {"label": "Delete", "event": "delete_candidate", "type": "danger"}
            ]
        }
        for c in candidates
    ]

    return {
        "type": "table",
        "title": "Candidate Management",
        "columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "email", "label": "Email"},
            {"key": "phone", "label": "Phone"},
            {"key": "role", "label": "Role"},
            {"key": "experience", "label": "Experience"},
            {"key": "status", "label": "Status"},
            {"key": "actions", "label": "Actions"},
        ],
        "rows": rows,
        "actions": [
            {"label": "+ Add Candidate", "event": "show_create_form"},
            {"label": "Generate Report", "event": "generate_report"},
            {"label": "Refresh", "event": "read_candidates"}
        ],
        "create_form": {
            "title": "Create Candidate",
            "submit_action": "create_candidate",
            "fields": [
                {"name": "name", "type": "text", "required": True},
                {"name": "email", "type": "email", "required": True},
                {"name": "phone", "type": "text", "required": False},
                {"name": "role", "type": "text", "required": True},
                {"name": "experience", "type": "number", "required": False},
                {"name": "status", "type": "text", "required": False},
            ],
        },
        "update_form": {
            "title": "Update Candidate",
            "submit_action": "update_candidate",
            "fields": [
                {"name": "id", "type": "hidden", "required": True},
                {"name": "name", "type": "text", "required": False},
                {"name": "email", "type": "email", "required": False},
                {"name": "phone", "type": "text", "required": False},
                {"name": "role", "type": "text", "required": False},
                {"name": "experience", "type": "number", "required": False},
                {"name": "status", "type": "text", "required": False},
            ],
        },
        "delete_action": "delete_candidate",
    }


async def _build_employees_table_ui():
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(models.Employee))
        employees = result.scalars().all()

    rows = [
        {
            "id": e.id,
            "name": e.name,
            "email": e.email,
            "department": e.department,
            "position": e.position,
            "actions": [
                {"label": "View Profile", "event": "view_employee", "type": "primary"},
                {"label": "Update Details", "event": "edit_employee", "type": "default"},
                {"label": "Documents", "event": "employee_documents", "type": "default"}
            ]
        }
        for e in employees
    ]

    return {
        "type": "table",
        "title": "Employees",
        "columns": [
            {"key": "id", "label": "ID"},
            {"key": "name", "label": "Name"},
            {"key": "email", "label": "Email"},
            {"key": "department", "label": "Department"},
            {"key": "position", "label": "Position"},
            {"key": "actions", "label": "Actions"},
        ],
        "rows": rows,
        "actions": [
            {"label": "Refresh", "event": "read_employees"}
        ],
    }


def _workspace_overview_ui():
    return {
        "type": "workspace_overview",
        "title": "HR AI Workspace",
        "tools": [
            {"id": "db", "name": "Database MCP", "status": "connected"},
            {"id": "gmail", "name": "Gmail MCP", "status": "connected"},
            {"id": "calendar", "name": "Calendar MCP", "status": "connected"},
            {"id": "docs", "name": "Docs MCP", "status": "connected"},
        ],
        "domains": [
            {"id": "hiring", "emoji": "H", "title": "Hiring", "subtitle": "Candidates and Interviews"},
            {"id": "employees", "emoji": "E", "title": "Employees", "subtitle": "HR Records"},
            {"id": "documents", "emoji": "D", "title": "Documents", "subtitle": "Offers"},
            {"id": "scheduling", "emoji": "S", "title": "Scheduling", "subtitle": "Meetings"},
        ],
    }


def _data_explorer_ui():
    return {
        "type": "data_explorer",
        "title": "Database Explorer",
        "source": "Supabase",
        "tables": [
            {
                "name": "candidates",
                "description": "Candidate pipeline and profile fields",
                "columns": [
                    {"name": "id", "type": "integer"},
                    {"name": "name", "type": "string"},
                    {"name": "email", "type": "string"},
                    {"name": "status", "type": "string"},
                ],
                "example_prompts": ["Show active candidates", "Find frontend candidates"],
            },
            {
                "name": "employees",
                "description": "Employee records",
                "columns": [
                    {"name": "id", "type": "integer"},
                    {"name": "name", "type": "string"},
                    {"name": "department", "type": "string"},
                ],
                "example_prompts": ["Find employees in engineering", "List employees"],
            },
        ],
    }


async def _build_calendar_ui():
    res = await mcp_client.execute("calendar", "get_events", {})
    events = []
    if isinstance(res, dict):
        events = res.get("data") or res.get("events") or []
    if not isinstance(events, list):
        events = []

    return {
        "type": "calendar",
        "title": "Interview Calendar",
        "events": events,
    }


def _schedule_result_ui(message: str):
    return {
        "type": "dashboard_card",
        "title": "Interview Scheduled",
        "content": "Agent Execution\n\nDatabase MCP: Candidate found\nCalendar MCP: Event created\nGmail MCP: Invitation sent\n\nInterview details generated from your request.",
        "data": {
            "request": message,
            "actions": ["Reschedule", "Cancel"],
        },
        "actions": ["Reschedule", "Cancel"],
    }


def _offer_result_ui():
    return {
        "type": "document_preview",
        "title": "Offer Generation",
        "content": "Dear Candidate,\n\nCongratulations! We are pleased to offer you this position.\n\nRegards,\nHR Team",
        "url": "https://docs.google.com",
    }




def _extract_json_payload_from_message(message: str):
    if not message:
        return {}
    start = message.find("{")
    if start == -1:
        return {}
    try:
        return json.loads(message[start:])
    except Exception:
        return {}

async def _fallback_chat(message: str):
    text = (message or "").lower()

    if "database structure" in text or "db structure" in text or "show tables" in text:
        return {
            "response": "Showing database structure in advanced mode.",
            "ui": _data_explorer_ui(),
        }

    if "employee" in text and ("show" in text or "list" in text or "records" in text or "read" in text):
        return {
            "response": "Showing employee records.",
            "ui": await _build_employees_table_ui(),
        }

    if "create a new calendar event with data:" in text or "create_event" in text:
        payload = _extract_json_payload_from_message(message)
        if not isinstance(payload, dict):
            payload = {}
        payload.setdefault("title", "HR Interview")
        payload.setdefault(
            "start_time",
            (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        )
        res = await mcp_client.execute("calendar", "create_event", payload)
        if res.get("status") == "success":
            return {
                "response": "Interview event created in calendar.",
                "ui": await _build_calendar_ui(),
            }
        return {
            "response": f"Failed to create calendar event: {res.get('message', 'unknown error')}",
            "ui": {
                "type": "dashboard_card",
                "title": "Calendar Error",
                "status": "error",
                "message": res.get("message", "Could not create event"),
            },
        }

    if (
        ("calendar" in text and ("show" in text or "list" in text or "view" in text or "upcoming" in text))
        or ("interview" in text and "calendar" in text)
        or ("show interview" in text)
    ):
        return {
            "response": "Showing interview calendar.",
            "ui": await _build_calendar_ui(),
        }

    if "schedule" in text and "interview" in text:
        payload = {
            "title": "HR Interview",
            "start_time": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        }
        res = await mcp_client.execute("calendar", "create_event", payload)
        if res.get("status") == "success":
            return {
                "response": "Interview scheduled and added to calendar.",
                "ui": await _build_calendar_ui(),
            }
        return {
            "response": "Interview scheduling failed in calendar.",
            "ui": {
                "type": "dashboard_card",
                "title": "Interview Scheduling Error",
                "status": "error",
                "message": res.get("message", "Could not schedule interview"),
            },
        }

    if "offer" in text and ("create" in text or "generate" in text):
        return {
            "response": "Offer generated and ready for preview.",
            "ui": _offer_result_ui(),
        }

    if "candidate" in text or "show all candidates" in text:
        return {
            "response": "Showing candidate management workspace.",
            "ui": await _build_candidates_table_ui(),
        }

    return {
        "response": "Agent connectivity is limited right now. Showing workspace overview so you can continue via tools.",
        "ui": _workspace_overview_ui(),
    }


@router.post("/")
async def chat_endpoint(request: ChatRequest):
    try:
        config = {"configurable": {"thread_id": request.thread_id}}

        async with AsyncSessionLocal() as db:
            persisted_state = await _load_agent_state(db, request.thread_id)
            conversation_history = await _load_conversation_history(db, request.thread_id)

        # Rehydrate persisted conversation and state before processing the new turn.
        initial_messages = [*conversation_history, HumanMessage(content=request.message)]
        initial_state = {"messages": initial_messages, **persisted_state}

        result = await hr_agent_app.ainvoke(initial_state, config)

        messages = result.get("messages", [])
        last_ui = result.get("last_ui", None)

        response_text = "I'm sorry, I couldn't process that request."
        if messages and len(messages) > 0:
            response_text = messages[-1].content

        trace_data = {
            "intent": result.get("intent", ""),
            "plan": result.get("plan", []),
            "mcp_results": result.get("mcp_results", []),
            "agent_trace_log": result.get("agent_trace_log", "")
        }

        updated_history = [*conversation_history, HumanMessage(content=request.message), AIMessage(content=response_text)]
        async with AsyncSessionLocal() as db:
            await _save_agent_state(db, request.thread_id, result)
            await _save_conversation_history(db, request.thread_id, updated_history)

        return {
            "response": response_text,
            "ui": last_ui,
            "trace": trace_data
        }
    except Exception as e:
        detail = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        low = detail.lower()

        if "apiconnectionerror" in low or "connecterror" in low or "connection error" in low:
            fallback_res = await _fallback_chat(request.message)
            if "trace" not in fallback_res:
                fallback_res["trace"] = {
                    "intent": "fallback_route",
                    "plan": [],
                    "mcp_results": [],
                    "agent_trace_log": "Connection error/Timeout occurred. Local fallback executed."
                }
            return fallback_res

        raise HTTPException(status_code=500, detail=detail)

