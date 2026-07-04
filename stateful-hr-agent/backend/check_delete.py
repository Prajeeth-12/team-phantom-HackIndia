import asyncio
from dotenv import load_dotenv
load_dotenv()
from app.agent.graph import hr_agent_app
from langchain_core.messages import HumanMessage
from app.database.database import AsyncSessionLocal
from sqlalchemy import text

async def main():
    config = {'configurable': {'thread_id': 'test-delete'}}
    inputs = {'messages': [HumanMessage(content='Delete Priya')]}
    async for event in hr_agent_app.astream(inputs, config, stream_mode='values'):
        pass
        
    async with AsyncSessionLocal() as db:
        p = await db.execute(text("SELECT id FROM candidates WHERE name ILIKE '%Priya%'"))
        priya = p.fetchone()
        print('Priya Exists:', priya)

asyncio.run(main())
