import asyncio
import os
import json
from dotenv import load_dotenv
load_dotenv()

from app.agent.graph import hr_agent_app
from langchain_core.messages import HumanMessage
from app.database.database import AsyncSessionLocal
from sqlalchemy import text

async def run_test(test_name: str, message: str, thread_id: str):
    print(f"\n\n==================================")
    print(f"TEST: {test_name}")
    print(f"==================================")
    
    config = {'configurable': {'thread_id': thread_id}}
    inputs = {'messages': [HumanMessage(content=message)]}
    
    try:
        async for event in hr_agent_app.astream(inputs, config, stream_mode='values'):
            pass
    except Exception as e:
        print(f"FAILED WITH EXCEPTION: {e}")

async def setup_test_data():
    # Make sure Priya and Rahul exist before tests
    async with AsyncSessionLocal() as db:
        await db.execute(text("INSERT INTO candidates (name, email, role, status) VALUES ('Priya', 'priya@test.com', 'Data Scientist', 'applied') ON CONFLICT DO NOTHING"))
        await db.execute(text("INSERT INTO candidates (name, email, role, status) VALUES ('Rahul', 'rahul@test.com', 'Backend Engineer', 'interviewing') ON CONFLICT DO NOTHING"))
        await db.commit()

async def verify_no_priya():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT id FROM candidates WHERE name ILIKE '%Priya%'"))
        row = res.fetchone()
        return row is None

async def verify_rahul_employee():
    async with AsyncSessionLocal() as db:
        res = await db.execute(text("SELECT status FROM candidates WHERE name ILIKE '%Rahul%'"))
        row = res.fetchone()
        return row is not None and row[0] == 'hired' # assuming convert updates status to hired or something, let's see. Or checks employees table.

async def main():
    await setup_test_data()
    thread_id = "test-e2e-execution-final"
    
    print("\n\n##################################")
    print("STARTING E2E EXECUTION TESTS")
    print("##################################\n")
    
    # 1. Show candidates (to test context)
    await run_test("PRE-TEST: Show candidates", "Show all candidates", thread_id)
    
    # 2. Offer for Priya
    await run_test("COMMAND: OFFER", "Generate offer letter for Priya", thread_id)
    
    # 3. Schedule Rahul
    await run_test("COMMAND: INTERVIEW", "Schedule interview for Rahul tomorrow 5 PM", thread_id)
    
    # 4. Convert Rahul
    await run_test("COMMAND: CONVERT", "Move Rahul to employee", thread_id)
    
    # 5. Delete Priya
    await run_test("COMMAND: DELETE", "Delete Priya", thread_id)

if __name__ == "__main__":
    asyncio.run(main())
