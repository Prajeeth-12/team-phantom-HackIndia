# Stateful AI HR Agent Platform - Context

## Project Overview
This project is an AI-driven HR Agent platform built for a hackathon. The system behaves like an autonomous HR employee that manages candidates, schedules interviews, generates offer letters, and converts candidates to employees. 
Instead of a standard conversational chatbot, it features a "Dynamic Workspace" where an AI LLM generates interactive UI components (AG-UI) on the fly based on backend state and user intent.

## Tech Stack
* **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS, shadcn/ui (AG-UI schema rendering)
* **Backend**: Python FastAPI
* **Agent Engine**: LangGraph, OpenAI (Azure/GPT-5.1/GPT-4o-mini)
* **Database**: PostgreSQL (Supabase) + SQLAlchemy
* **Integrations**: Google Calendar (for scheduling), Google Docs (for offers), Gmail (for emails)

## System Architecture
1. **Frontend (`/frontend`)**: A pure AG-UI renderer. The user submits a request via the Command Center chat, and the frontend sends it to the backend. It receives a JSON schema (`uiConfig`) and renders dynamic components (`DynamicTable`, `DynamicForm`, etc.). It also handles inline edits and action events, forwarding them back to the backend.
2. **Backend (`/backend`)**: Hosts the FastAPI server and the LangGraph agent. 
   * `app.agent.graph`: The core LangGraph workflow.
   * `app.agent.ui_generator`: Converts backend context and tool execution results into structured AG-UI schemas.
   * `app.mcp`: Implements external tool integrations (PostgreSQL, Calendar, Gmail, Docs).

## Current State & Recent Accomplishments
* **UI/UX Overhaul**: Transitioned from a raw JSON/CRUD-focused UI to a polished, product-like HR workspace. Global CRUD buttons (Read, Create, Update, Delete) were removed and replaced with contextual workspace actions (e.g., "+ Add Candidate", "Generate Report").
* **Inline Edits**: `DynamicTable.tsx` supports inline editing of rows, sending updates to the backend cleanly.
* **Action Buttons**: Table cells that contain arrays of action objects (e.g., View Profile, Schedule Interview, Delete) now render as interactive buttons.
* **Agent Execution Trace**: Raw agent reasoning, intents, and MCP tool payloads are no longer dumped directly in the chat. Instead, they are hidden behind a collapsible "View Agent Steps" UI to maintain a clean aesthetic while allowing debugging.
* **Entity Resolution First**: The agent enforces a strict workflow where it must resolve entities (e.g., `get_candidates`) before acting (e.g., `schedule_interview`), ensuring it doesn't ask the user for database IDs.

## Next Steps / Focus Areas
* **Continue E2E Testing**: Ensure all flows (Delete Candidate, Convert Employee, Schedule Interview) update the database correctly and the frontend refreshes seamlessly.
* **UI Polish**: Ensure the frontend continues to look premium, dynamic, and responsive without exposing raw backend traces or unformatted JSON objects.
* **Bug Fixes**: Monitor `DynamicTable` and `DynamicRenderer` for any state desync issues during inline editing or form submissions.

## Useful Commands
* **Run Backend**: `cd backend && .\venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000`
* **Run Frontend**: `cd frontend && npm run dev`
* **Run with Docker**: `docker compose up --build`
