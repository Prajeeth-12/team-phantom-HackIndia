import asyncio
from dotenv import load_dotenv
load_dotenv()
from app.database.database import AsyncSessionLocal
from sqlalchemy import text

async def main():
    async with AsyncSessionLocal() as db:
        await db.execute(text("INSERT INTO candidates (name, email, role, status) VALUES ('Priya', 'priya@test.com', 'Data Scientist', 'applied') ON CONFLICT DO NOTHING"))
        await db.commit()
asyncio.run(main())
