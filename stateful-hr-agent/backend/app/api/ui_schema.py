from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.database import get_db
from app.database.repository import candidate_repo

router = APIRouter(prefix="/api/ui-schema", tags=["ui-schema"])


@router.get("/candidates")
async def candidates_ui_schema(db: AsyncSession = Depends(get_db)):
    """Return AG-UI schema for proper tab-based CRUD operations."""
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
