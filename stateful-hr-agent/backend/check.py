import asyncio
from dotenv import load_dotenv
load_dotenv()
from app.database.database import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as db:
        r = await db.execute(text("SELECT id, status FROM candidates WHERE name ILIKE '%Rahul%'"))
        rahul = r.fetchone()
        p = await db.execute(text("SELECT id FROM candidates WHERE name ILIKE '%Priya%'"))
        priya = p.fetchone()
        
        print('Rahul Status:', rahul)
        print('Priya Exists:', priya)

asyncio.run(main())
