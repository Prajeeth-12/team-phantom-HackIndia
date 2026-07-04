from typing import Dict, Any
import os
import base64
from email.message import EmailMessage
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.send']

def get_credentials():
    creds = None
    if os.path.exists('token_gmail.json'):
        creds = Credentials.from_authorized_user_file('token_gmail.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("Google OAuth credentials.json not found. Please add your credentials from GCP.")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token_gmail.json', 'w') as token:
            token.write(creds.to_json())
    return creds

async def execute_gmail(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Real Gmail MCP Server using OAuth.
    """
    if action == "send_email":
        try:
            creds = get_credentials()
            service = build('gmail', 'v1', credentials=creds)
            
            message = EmailMessage()
            message.set_content(payload.get("body", "Please find the details of your interview attached."))
            message['To'] = payload.get("to")
            message['Subject'] = payload.get("subject", "HR Interview Details")
            
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            create_message = {'raw': encoded_message}
            
            send_message = service.users().messages().send(userId="me", body=create_message).execute()
            
            return {
                "status": "success",
                "message": "Email sent successfully via Gmail API",
                "data": {
                    "to": payload.get("to"),
                    "message_id": send_message.get('id')
                }
            }
        except Exception as e:
             return {"status": "error", "message": f"Gmail API Error: {str(e)}"}
             
    elif action == "create_draft":
        return {"status": "success", "message": "Draft created in Gmail (mock)"}
             
    return {"status": "error", "message": f"Unknown action: {action}"}
