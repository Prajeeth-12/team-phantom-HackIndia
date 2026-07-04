import os
import asyncio
from dotenv import load_dotenv
load_dotenv(dotenv_path="../.env") # Assuming running from backend folder

from app.services.llm import get_agent_llm

async def test_azure():
    print("Testing Azure OpenAI connection...")
    try:
        llm = get_agent_llm()
        res = await llm.ainvoke("Say exactly 'HR Agent Ready'")
        print(res.content)
    except Exception as e:
        print(f"Error connecting to Azure: {e}")

if __name__ == "__main__":
    asyncio.run(test_azure())
