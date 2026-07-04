from typing import Dict, Any
from app.database.database import AsyncSessionLocal
from app.database.repository import candidate_repo
from app.schemas import schemas

async def execute_postgres(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mock Postgres MCP Server
    Will be replaced by a standalone MCP service later.
    Currently executes DB operations indirectly for the Agent.
    """
    async with AsyncSessionLocal() as db:
        if action == "create_candidate":
            candidate_data = schemas.CandidateCreate(**payload)
            db_candidate = await candidate_repo.create_candidate(db, candidate_data)
            return {"status": "success", "data": {"id": db_candidate.id, "name": db_candidate.name}}
            
        elif action == "get_candidates":
            skip = payload.get("skip", 0)
            limit = payload.get("limit", 100)
            candidates = await candidate_repo.get_candidates(db, skip, limit)
            result = [{"id": c.id, "name": c.name, "status": c.status} for c in candidates]
            return {"status": "success", "data": result}
            
        elif action == "update_candidate":
            candidate_id = payload.get("id")
            if not candidate_id:
                return {"status": "error", "message": "candidate id required"}
            update_data = schemas.CandidateUpdate(**payload.get("data", {}))
            db_candidate = await candidate_repo.update_candidate(db, candidate_id, update_data)
            if db_candidate:
                return {"status": "success", "data": {"id": db_candidate.id, "status": db_candidate.status}}
            return {"status": "error", "message": "candidate not found"}
            
        elif action == "delete_candidate":
            candidate_id = payload.get("id")
            if not candidate_id:
                return {"status": "error", "message": "candidate id required"}
            db_candidate = await candidate_repo.delete_candidate(db, candidate_id)
            if db_candidate:
                return {"status": "success", "message": "Candidate deleted"}
            return {"status": "error", "message": "candidate not found"}
            
        elif action == "convert_to_employee":
            candidate_id = payload.get("id")
            if not candidate_id:
                return {"status": "error", "message": "candidate id required"}
            db_candidate = await candidate_repo.get_candidate(db, candidate_id)
            if db_candidate:
                from app.database import models
                employee = models.Employee(
                    name=db_candidate.name,
                    email=db_candidate.email,
                    department="Engineering", # default for demo
                    position=db_candidate.role
                )
                db.add(employee)
                # optionally delete the candidate here
                await candidate_repo.delete_candidate(db, candidate_id)
                await db.commit()
                return {"status": "success", "message": f"{db_candidate.name} officially converted to an Employee!"}
            return {"status": "error", "message": "candidate not found"}
            
        elif action == "create_employee":
            # Direct creation
            return {"status": "success", "message": "Employee created directly (mock)"}
            
        elif action == "create_interview":
            # Mocking interview creation since we didn't fully implement interview repo yet
            candidate_id = payload.get("candidate_id")
            return {
                "status": "success", 
                "data": {
                    "candidate_id": candidate_id, 
                    "interview_id": 999, 
                    "scheduled_time": payload.get("scheduled_time"),
                    "meeting_link": "https://meet.google.com/mock-link"
                }
            }
            
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}
