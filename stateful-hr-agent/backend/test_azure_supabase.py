import asyncio
import httpx

from app.main import app
from app.services.llm import get_agent_llm, get_fast_llm
import traceback
import sys

async def test_azure():
    print("\n--- 1A. Azure Test ---")
    try:
        agent_llm = get_agent_llm()
        fast_llm = get_fast_llm()
        
        # Test GPT-5.1
        print("Testing GPT-5.1 (Agent LLM)...")
        res_agent = await agent_llm.ainvoke("Say the word 'PASS' and nothing else.")
        print(f"GPT-5.1 response: {res_agent.content.strip()}")
        
        # Test GPT-5-mini
        print("Testing GPT-5-mini (Fast LLM)...")
        res_fast = await fast_llm.ainvoke("Say the word 'PASS' and nothing else.")
        print(f"GPT-5-mini response: {res_fast.content.strip()}")
        
        print("Azure Test: SUCCESS")
    except Exception as e:
        print(f"Azure Test: FAILED - {e}")
        traceback.print_exc()

async def test_supabase():
    print("\n--- 1B. Supabase Test ---")
    created_id = None
    try:
        import random
        random_suffix = random.randint(1000, 9999)
        # We use ASyncClient with the FastAPI app, directly
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            # 1. Create: Candidate Rahul
            print("Testing CREATE...")
            candidate_data = {
                "name": "Candidate Rahul",
                "email": f"rahul.test.{random_suffix}@example.com",
                "experience": 3,
                "role": "Software Engineer",
                "skills": "Python, FastAPI",
                "status": "applied"
            }
            res_create = await client.post("/api/candidates/", json=candidate_data)
            assert res_create.status_code == 200, f"Failed to create: {res_create.text}"
            created_candidate = res_create.json()
            created_id = created_candidate["id"]
            print(f"Created candidate: {created_candidate['name']} with ID {created_id}")

            # 2. Read: SELECT candidates
            print("Testing READ...")
            res_read = await client.get("/api/candidates/")
            assert res_read.status_code == 200, f"Failed to read: {res_read.text}"
            candidates = res_read.json()
            print(f"Read {len(candidates)} candidates.")
            
            # 3. Update: experience 3 -> 5
            print("Testing UPDATE...")
            update_data = {"experience": 5}
            res_update = await client.patch(f"/api/candidates/{created_id}", json=update_data)
            assert res_update.status_code == 200, f"Failed to update: {res_update.text}"
            updated_candidate = res_update.json()
            assert updated_candidate["experience"] == 5, "Experience not updated"
            print(f"Updated candidate experience to {updated_candidate['experience']}")

            # 4. Delete: remove test user
            print("Testing DELETE...")
            res_delete = await client.delete(f"/api/candidates/{created_id}")
            assert res_delete.status_code == 200, f"Failed to delete: {res_delete.text}"
            print("Deleted test user successfully.")
            
            print("Supabase Test: SUCCESS")
    except Exception as e:
        print(f"Supabase Test: FAILED - {e}")
        traceback.print_exc()
        
        # Cleanup if failed after create
        if created_id:
            try:
                transport = httpx.ASGITransport(app=app)
                async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
                    await client.delete(f"/api/candidates/{created_id}")
            except:
                pass

async def main():
    await test_azure()
    await test_supabase()

if __name__ == "__main__":
    # Windows asyncio loop fix for ProactorEventLoop issue
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
