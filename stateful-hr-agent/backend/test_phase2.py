import requests
import json
import time
import subprocess
import os

def test_workflow():
    print("\n--- 2. Postgres MCP + AG-UI Candidate Workflow ---")
    
    print("Starting uvicorn server...")
    server_process = subprocess.Popen(
        [r".\venv\Scripts\uvicorn.exe", "app.main:app", "--host", "127.0.0.1", "--port", "8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True
    )
    
    # Wait for server to be ready
    started = False
    start_wait = time.time()
    while time.time() - start_wait < 20:
        line = server_process.stdout.readline()
        if line:
            print("SERVER:", line.strip())
            if "Application startup complete." in line:
                started = True
                break
        time.sleep(0.1)
        
    if not started:
        print("Server failed to start in time!")
        server_process.terminate()
        return
        
    url = "http://127.0.0.1:8000/api/chat/"
    payload = {
        "message": "Show all candidates",
        "thread_id": "test_phase2_thread"
    }
    
    print("Sending message: 'Show all candidates' to /api/chat/...")
    try:
        response = requests.post(url, json=payload, timeout=60.0)
        if response.status_code == 200:
            data = response.json()
            print("\nAPI Response received!")
            print(f"Agent Reply: {data.get('response')}")
            ui_config = data.get('ui')
            if ui_config:
                print("\nUI Config generated successfully:")
                print(json.dumps(ui_config, indent=2))
            else:
                print("\nNo UI Config generated.")
        else:
            print(f"\nAPI Error {response.status_code}: {response.text}")
    except Exception as e:
        print(f"\nRequest failed: {e}")
    finally:
        print("Shutting down uvicorn server...")
        server_process.terminate()
        server_process.wait()
        stderr_output = server_process.stderr.read().decode('utf-8')
        if stderr_output:
            print("Server stderr:")
            print(stderr_output)

if __name__ == "__main__":
    test_workflow()
