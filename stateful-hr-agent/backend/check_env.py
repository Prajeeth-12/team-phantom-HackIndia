import os, sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
env_path = Path(__file__).resolve().parents[1] / ".env"
loaded = load_dotenv(dotenv_path=env_path, override=True)

print(f"=== ENV FILE ===")
print(f"  Path : {env_path}")
print(f"  Found: {env_path.exists()}")
print(f"  Loaded: {loaded}")
print()

required = {
    "DATABASE_URL":                  os.getenv("DATABASE_URL"),
    "AZURE_OPENAI_API_KEY":          os.getenv("AZURE_OPENAI_API_KEY"),
    "AZURE_OPENAI_ENDPOINT":         os.getenv("AZURE_OPENAI_ENDPOINT"),
    "AZURE_OPENAI_API_VERSION":      os.getenv("AZURE_OPENAI_API_VERSION"),
    "AZURE_OPENAI_AGENT_DEPLOYMENT": os.getenv("AZURE_OPENAI_AGENT_DEPLOYMENT"),
    "AZURE_OPENAI_FAST_DEPLOYMENT":  os.getenv("AZURE_OPENAI_FAST_DEPLOYMENT"),
    "SUPABASE_URL":                  os.getenv("SUPABASE_URL"),
    "SUPABASE_SERVICE_ROLE_KEY":     os.getenv("SUPABASE_SERVICE_ROLE_KEY"),
    "SUPABASE_BUCKET":               os.getenv("SUPABASE_BUCKET"),
    "GOOGLE_CREDENTIALS_FILE":       os.getenv("GOOGLE_CREDENTIALS_FILE"),
    "FRONTEND_URL":                  os.getenv("FRONTEND_URL"),
    "BACKEND_PORT":                  os.getenv("BACKEND_PORT"),
}

print("=== VARIABLE AUDIT ===")
missing = []
for k, v in required.items():
    if not v:
        missing.append(k)
        print(f"  [MISSING] {k}")
    else:
        if len(v) > 14:
            masked = v[:6] + "***" + v[-4:]
        else:
            masked = "****"
        print(f"  [OK]      {k} = {masked}")

# Check credentials.json path
print()
print("=== GOOGLE CREDENTIALS FILE ===")
creds_var = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
backend_dir = Path(__file__).resolve().parent
root_dir = backend_dir.parent

for label, path in [("backend/", backend_dir / creds_var), ("root/", root_dir / creds_var)]:
    status = "FOUND" if path.exists() else "NOT FOUND"
    print(f"  [{status}] {label}{creds_var} -> {path}")

# Check DATABASE_URL is not localhost default
print()
print("=== DATABASE URL CHECK ===")
db_url = os.getenv("DATABASE_URL", "")
if "localhost" in db_url and "supabase" not in db_url:
    print("  [WARN] DATABASE_URL points to localhost — may not be Supabase")
elif "supabase" in db_url or "pooler" in db_url:
    print("  [OK]  DATABASE_URL points to Supabase pooler")
else:
    print(f"  [INFO] DATABASE_URL = {db_url[:40]}...")

# Check API_VERSION compatibility
print()
print("=== API VERSION CHECK ===")
api_ver = os.getenv("AZURE_OPENAI_API_VERSION", "")
recommended = "2024-02-15-preview"
if api_ver == recommended or "preview" in api_ver:
    print(f"  [OK]  AZURE_OPENAI_API_VERSION = {api_ver}")
else:
    print(f"  [WARN] API version '{api_ver}' — expected a preview version like {recommended}")

# Final verdict
print()
print("=== RESULT ===")
if not missing:
    print('  {"environment": "ready"}')
    sys.exit(0)
else:
    print(f'  {{"environment": "error", "missing": {missing}}}')
    sys.exit(1)
