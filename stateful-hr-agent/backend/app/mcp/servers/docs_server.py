from typing import Dict, Any
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/documents', 'https://www.googleapis.com/auth/drive.file']

def get_credentials():
    creds = None
    if os.path.exists('token_docs.json'):
        creds = Credentials.from_authorized_user_file('token_docs.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("Google OAuth credentials.json not found. Please add your credentials from GCP.")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token_docs.json', 'w') as token:
            token.write(creds.to_json())
    return creds

async def execute_docs(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Real Google Docs MCP Server using OAuth.
    """
    if action == "generate_document":
        try:
            creds = get_credentials()
            docs_service = build('docs', 'v1', credentials=creds)
            drive_service = build('drive', 'v3', credentials=creds)
            
            doc_type = payload.get("type", "offer_letter")
            candidate_name = payload.get("candidate_name", "Candidate")
            title = f"{candidate_name} - {doc_type.replace('_', ' ').title()}"
            
            # Create a blank document
            document = docs_service.documents().create(body={'title': title}).execute()
            doc_id = document.get('documentId')
            
            # Insert basic content for the Offer Letter
            content = f"Official {doc_type.replace('_', ' ').title()}\n\nDear {candidate_name},\n\nWe are extremely pleased to offer you this position. Welcome to the team!"
            requests = [
                {
                    'insertText': {
                        'location': {'index': 1},
                        'text': content
                    }
                }
            ]
            docs_service.documents().batchUpdate(documentId=doc_id, body={'requests': requests}).execute()
            
            # Adjust permissions so anyone with link can view it (useful for rendering preview)
            drive_service.permissions().create(
                fileId=doc_id,
                body={'type': 'anyone', 'role': 'reader'}
            ).execute()
            
            doc_url = f"https://docs.google.com/document/d/{doc_id}/view"
            
            return {
                "status": "success",
                "message": "Document generated successfully via Google Docs API",
                "data": {
                    "document_id": doc_id,
                    "document_url": doc_url,
                    "type": doc_type
                }
            }
        except Exception as e:
            return {"status": "error", "message": f"Docs API Error: {str(e)}"}
            
    elif action == "update_document":
        return {"status": "success", "message": "Document updated (mock)"}
            
    return {"status": "error", "message": f"Unknown action: {action}"}
