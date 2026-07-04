import asyncio
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env")

from app.database.database import engine, Base
# Import models to ensure they are registered with Base
from app.database import models

async def init_models():
    print("Connecting to Supabase and creating tables...")
    try:
        async with engine.begin() as conn:
            # We use create_all. It won't drop existing data if tables exist.
            await conn.run_sync(Base.metadata.create_all)
        print("Successfully synchronized models to Supabase!")
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    asyncio.run(init_models())
