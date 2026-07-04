import asyncio
import datetime
from app.mcp.servers.gmail_server import execute_gmail
from app.mcp.servers.calendar_server import execute_calendar
from app.mcp.servers.docs_server import execute_docs

async def test_google_apis():
    print("\n--- 1C. Google APIs Test ---")
    
    # 1. Test Gmail
    print("\n[1] Testing Gmail API...")
    gmail_payload = {
        "to": "test@example.com",
        "subject": "Test from HR Agent",
        "body": "This is a test email."
    }
    try:
        res = await execute_gmail("send_email", gmail_payload)
        if res.get("status") == "success":
            print("PASS - Gmail API")
        else:
            print(f"FAILED - Gmail API: {res.get('message')}")
    except Exception as e:
        print(f"FAILED - Gmail API: {str(e)}")

    # 2. Test Calendar
    print("\n[2] Testing Calendar API...")
    now = datetime.datetime.utcnow()
    # add 24 hours to schedule the interview tomorrow
    start_time = (now + datetime.timedelta(days=1)).isoformat() + "Z"
    calendar_payload = {
        "title": "Test Interview Event",
        "start_time": start_time,
        "attendees": ["test@example.com"]
    }
    try:
        res = await execute_calendar("create_event", calendar_payload)
        if res.get("status") == "success":
            print("PASS - Calendar API")
        else:
            print(f"FAILED - Calendar API: {res.get('message')}")
    except Exception as e:
        print(f"FAILED - Calendar API: {str(e)}")

    # 3. Test Docs & Drive
    print("\n[3] Testing Docs & Drive API...")
    docs_payload = {
        "type": "test_document",
        "candidate_name": "Test Candidate"
    }
    try:
        res = await execute_docs("generate_document", docs_payload)
        if res.get("status") == "success":
            print("PASS - Docs API")
            print("PASS - Drive API (Permissions adjusted via Drive API in docs_server)")
        else:
            print(f"FAILED - Docs/Drive API: {res.get('message')}")
    except Exception as e:
        print(f"FAILED - Docs/Drive API: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_google_apis())
