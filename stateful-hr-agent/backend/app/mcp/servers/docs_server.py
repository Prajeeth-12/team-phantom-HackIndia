from typing import Any, Dict
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/documents", "https://www.googleapis.com/auth/drive.file"]


def get_credentials():
    creds = None
    if os.path.exists("token_docs.json"):
        creds = Credentials.from_authorized_user_file("token_docs.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists("credentials.json"):
                raise FileNotFoundError("Google OAuth credentials.json not found. Please add your credentials from GCP.")
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token_docs.json", "w") as token:
            token.write(creds.to_json())
    return creds


async def execute_docs(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Real Google Docs MCP Server using OAuth.
    """
    try:
        creds = get_credentials()
        docs_service = build("docs", "v1", credentials=creds)
        drive_service = build("drive", "v3", credentials=creds)

        if action in {"create_document", "generate_document"}:
            doc_type = payload.get("type", "offer_letter")
            candidate_name = payload.get("candidate_name", "Candidate")
            title = payload.get("title") or f"{candidate_name} - {doc_type.replace('_', ' ').title()}"

            document = docs_service.documents().create(body={"title": title}).execute()
            doc_id = document.get("documentId")

            content = payload.get("content") or (
                f"Official {doc_type.replace('_', ' ').title()}\n\n"
                f"Dear {candidate_name},\n\n"
                "We are extremely pleased to offer you this position. Welcome to the team!"
            )
            requests = [{"insertText": {"location": {"index": 1}, "text": content}}]
            docs_service.documents().batchUpdate(documentId=doc_id, body={"requests": requests}).execute()

            drive_service.permissions().create(fileId=doc_id, body={"type": "anyone", "role": "reader"}).execute()
            doc_url = f"https://docs.google.com/document/d/{doc_id}/view"

            return {
                "status": "success",
                "message": "Document generated successfully via Google Docs API",
                "data": {"document_id": doc_id, "document_url": doc_url, "type": doc_type},
            }

        if action == "update_document":
            document_id = payload.get("document_id")
            content = payload.get("content")
            if not document_id or not content:
                return {"status": "error", "message": "document_id and content are required for update_document"}

            requests = [{"insertText": {"endOfSegmentLocation": {}, "text": f"\n\n{content}"}}]
            docs_service.documents().batchUpdate(documentId=document_id, body={"requests": requests}).execute()
            return {"status": "success", "message": "Document updated successfully", "data": {"document_id": document_id}}

        if action == "get_dashboard_metrics":
            # For hackathon purposes, search Drive for recent documents
            results = drive_service.files().list(
                q="mimeType='application/vnd.google-apps.document'",
                orderBy="createdTime desc",
                pageSize=100,
                fields="files(id, name, createdTime, webViewLink)"
            ).execute()
            items = results.get('files', [])
            
            generated_offers_count = len([i for i in items if 'offer' in i.get('name', '').lower()])
            latest_document = items[0].get('name') if items else "No documents found"
            
            return {
                "status": "success",
                "data": {
                    "documents": {
                        "generated_offers_count": generated_offers_count,
                        "latest_document": latest_document,
                        "total_documents": len(items)
                    }
                }
            }

        return {"status": "error", "message": f"Unknown action: {action}"}

    except Exception as e:
        return {"status": "error", "message": f"Docs API Error: {str(e)}"}
