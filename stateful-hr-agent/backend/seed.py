import asyncio
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

from sqlalchemy.future import select
from app.database.database import AsyncSessionLocal
from app.database.models import Candidate

async def seed():
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(Candidate))
            candidates = result.scalars().all()
            if not candidates:
                print("Seeding candidates...")
                c1 = Candidate(name="Rahul Sharma", email="rahul@example.com", role="Frontend Developer", experience=3, status="Screening")
                c2 = Candidate(name="Priya Nair", email="priya@example.com", role="AI Engineer", experience=2, status="Interview Scheduled")
                db.add_all([c1, c2])
                await db.commit()
                print("Seeded successfully!")
            else:
                print(f"Candidates already exist ({len(candidates)} found).")
    except Exception as e:
        print(f"Error seeding DB: {e}")

if __name__ == "__main__":
    asyncio.run(seed())
