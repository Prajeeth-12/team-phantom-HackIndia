from typing import Any, Dict

from app.database.database import AsyncSessionLocal
from app.database.repository import candidate_repo
from app.schemas import schemas


async def execute_postgres(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Postgres MCP server for candidate operations.
    """
    async with AsyncSessionLocal() as db:
        if action == "create_candidate":
            create_payload = dict(payload or {})
            if create_payload.get("name") and not create_payload.get("email"):
                safe_name = "".join(ch.lower() if ch.isalnum() else "." for ch in str(create_payload["name"]))
                while ".." in safe_name:
                    safe_name = safe_name.replace("..", ".")
                create_payload["email"] = f"{safe_name.strip('.')}@example.com"
            create_payload.setdefault("role", "Generalist")
            create_payload.setdefault("status", "applied")

            candidate_data = schemas.CandidateCreate(**create_payload)
            db_candidate = await candidate_repo.create_candidate(db, candidate_data)
            return {
                "status": "success",
                "data": {
                    "id": db_candidate.id,
                    "name": db_candidate.name,
                    "email": db_candidate.email,
                    "status": db_candidate.status,
                },
            }

        if action == "get_candidates":
            skip = payload.get("skip", 0)
            limit = payload.get("limit", 200)
            name_filter = (payload.get("name") or "").strip().lower()

            candidates = await candidate_repo.get_candidates(db, skip, limit)
            result = [
                {
                    "id": c.id,
                    "name": c.name,
                    "email": c.email,
                    "phone": c.phone,
                    "role": c.role,
                    "experience": c.experience,
                    "status": c.status,
                }
                for c in candidates
            ]
            if name_filter:
                result = [row for row in result if name_filter in str(row.get("name", "")).lower()]
            
            # Dynamically filter based on arbitrary user input (e.g. role, status, experience)
            for key, val in payload.items():
                if key not in ["skip", "limit", "name", "id"] and val:
                    if result and key in result[0]:
                        val_lower = str(val).lower()
                        result = [row for row in result if val_lower in str(row.get(key, "")).lower()]

            return {"status": "success", "data": result}

        if action == "get_employees":
            from sqlalchemy.future import select
            from app.database import models

            name_filter = (payload.get("name") or "").strip().lower()
            result = await db.execute(select(models.Employee))
            employees = result.scalars().all()
            data = [
                {
                    "id": e.id,
                    "name": e.name,
                    "email": e.email,
                    "department": e.department,
                    "position": e.position,
                }
                for e in employees
            ]
            if name_filter:
                data = [row for row in data if name_filter in str(row.get("name", "")).lower()]
                
            # Dynamically filter based on arbitrary user input (e.g. department, position)
            for key, val in payload.items():
                if key not in ["skip", "limit", "name", "id"] and val:
                    if data and key in data[0]:
                        val_lower = str(val).lower()
                        data = [row for row in data if val_lower in str(row.get(key, "")).lower()]

            return {"status": "success", "data": data}

        if action == "update_candidate":
            candidate_id = payload.get("id") or payload.get("candidate_id")
            if not candidate_id:
                return {"status": "error", "message": "candidate id required"}

            known_fields = {"name", "email", "phone", "role", "skills", "experience", "status", "resume_url"}
            
            data_dict = payload.get("data") or payload.get("update_data")
            if isinstance(data_dict, dict):
                update_raw = data_dict
            else:
                update_raw = {k: v for k, v in payload.items() if k in known_fields}
                
            update_data = schemas.CandidateUpdate(**(update_raw or {}))

            db_candidate = await candidate_repo.update_candidate(db, candidate_id, update_data)
            if db_candidate:
                return {
                    "status": "success",
                    "data": {
                        "id": db_candidate.id,
                        "name": db_candidate.name,
                        "email": db_candidate.email,
                        "status": db_candidate.status,
                    },
                }
            return {"status": "error", "message": "candidate not found"}

        if action == "convert_to_employee":
            candidate_id = payload.get("id") or payload.get("candidate_id")
            if not candidate_id:
                return {"status": "error", "message": "candidate id required for convert_to_employee"}

            from sqlalchemy.future import select
            from app.database import models

            # Fetch the candidate
            result = await db.execute(select(models.Candidate).where(models.Candidate.id == candidate_id))
            candidate = result.scalars().first()
            if not candidate:
                return {"status": "error", "message": "Candidate not found"}

            # Check if already an employee
            existing = await db.execute(select(models.Employee).where(models.Employee.email == candidate.email))
            if existing.scalars().first():
                return {"status": "success", "message": f"{candidate.name} is already an employee", "data": {"name": candidate.name, "email": candidate.email}}

            # Create employee record
            employee = models.Employee(
                name=candidate.name,
                email=candidate.email,
                department=payload.get("department", "Engineering"),
                position=candidate.role or payload.get("position", "Engineer"),
            )
            db.add(employee)

            # Update candidate status to hired
            candidate.status = "hired"
            await db.commit()
            await db.refresh(employee)

            return {
                "status": "success",
                "message": f"{candidate.name} has been converted to an employee",
                "data": {
                    "employee_id": employee.id,
                    "name": employee.name,
                    "email": employee.email,
                    "department": employee.department,
                    "position": employee.position,
                },
            }

        if action == "delete_candidate":
            candidate_id = payload.get("id")
            if not candidate_id:
                return {"status": "error", "message": "candidate id required"}
            db_candidate = await candidate_repo.delete_candidate(db, candidate_id)
            if db_candidate:
                return {"status": "success", "message": "Candidate deleted"}
            return {"status": "error", "message": "candidate not found"}

        if action == "get_dashboard_metrics":
            # Candidates metrics
            candidates = await candidate_repo.get_candidates(db, skip=0, limit=1000)
            total_candidates = len(candidates)
            applied_count = sum(1 for c in candidates if c.status.lower() == "applied")
            interviewing_count = sum(1 for c in candidates if c.status.lower() == "interviewing")
            selected_count = sum(1 for c in candidates if c.status.lower() == "selected")
            
            # Employees metrics
            from sqlalchemy import select
            from app.database import models
            result = await db.execute(select(models.Employee))
            employees = result.scalars().all()
            active_employee_count = len(employees)

            return {
                "status": "success",
                "data": {
                    "candidates": {
                        "total_candidates": total_candidates,
                        "applied_count": applied_count,
                        "interviewing_count": interviewing_count,
                        "selected_count": selected_count
                    },
                    "employees": {
                        "active_employee_count": active_employee_count
                    }
                }
            }

        return {"status": "error", "message": f"Unknown action: {action}"}
