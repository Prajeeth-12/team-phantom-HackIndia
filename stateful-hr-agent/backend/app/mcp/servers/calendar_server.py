from typing import Any, Dict
import os
import datetime
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar.events"]


def get_credentials():
    creds = None
    if os.path.exists("token_calendar.json"):
        creds = Credentials.from_authorized_user_file("token_calendar.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open("token_calendar.json", "w") as token:
                token.write(creds.to_json())
        else:
            return None
    return creds


async def execute_calendar(action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Real Google Calendar MCP Server using OAuth.
    """
    try:
        creds = get_credentials()
        if not creds:
            # Mock behavior if credentials don't exist
            if action == "get_events":
                return {
                    "status": "success",
                    "message": "Retrieved 1 mock events",
                    "data": [
                        {
                            "id": "mock-event-1",
                            "title": "Interview: John Doe",
                            "start": datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
                            "description": "Mock interview",
                            "meeting_link": "https://meet.google.com/mock"
                        }
                    ]
                }
            elif action == "create_event":
                return {"status": "success", "message": "Mock event created", "data": {"event_id": "mock-event-2"}}
            elif action in ["update_event", "cancel_event"]:
                return {"status": "success", "message": "Mock event updated/cancelled"}
            
        service = build("calendar", "v3", credentials=creds)

        if action == "get_events":
            now = datetime.datetime.utcnow().isoformat() + "Z"
            events_result = service.events().list(
                calendarId="primary",
                timeMin=now,
                maxResults=20,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            
            raw_events = events_result.get("items", [])
            formatted_events = []
            for item in raw_events:
                start = item.get("start", {}).get("dateTime", item.get("start", {}).get("date"))
                end = item.get("end", {}).get("dateTime", item.get("end", {}).get("date"))
                formatted_events.append({
                    "id": item.get("id"),
                    "title": item.get("summary", "Untitled Event"),
                    "start": start,
                    "end": end,
                    "description": item.get("description", ""),
                    "meeting_link": item.get("hangoutLink", "")
                })
                
            return {
                "status": "success",
                "message": f"Retrieved {len(formatted_events)} events",
                "data": formatted_events
            }

        if action == "create_event":
            title = payload.get("title", "HR Interview")
            start_time = payload.get("start_time") or datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
            start_dt = datetime.datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            end_dt = start_dt + datetime.timedelta(hours=1)

            attendees = [{"email": email} for email in payload.get("attendees", []) if email]

            event = {
                "summary": title,
                "start": {"dateTime": start_dt.isoformat(), "timeZone": "UTC"},
                "end": {"dateTime": end_dt.isoformat(), "timeZone": "UTC"},
                "attendees": attendees,
                "conferenceData": {
                    "createRequest": {
                        "requestId": f"req_{int(datetime.datetime.now().timestamp())}",
                        "conferenceSolutionKey": {"type": "hangoutsMeet"},
                    }
                },
            }

            event = service.events().insert(calendarId="primary", body=event, conferenceDataVersion=1).execute()
            return {
                "status": "success",
                "message": "Event created successfully",
                "data": {
                    "event_id": event.get("id"),
                    "meeting_link": event.get("hangoutLink", ""),
                    "start_time": start_time,
                },
            }

        if action == "update_event":
            event_id = payload.get("event_id")
            if not event_id:
                return {"status": "error", "message": "event_id is required for update_event"}

            patch: Dict[str, Any] = {}
            if payload.get("title"):
                patch["summary"] = payload["title"]
            if payload.get("start_time"):
                start_dt = datetime.datetime.fromisoformat(str(payload["start_time"]).replace("Z", "+00:00"))
                end_dt = start_dt + datetime.timedelta(hours=1)
                patch["start"] = {"dateTime": start_dt.isoformat(), "timeZone": "UTC"}
                patch["end"] = {"dateTime": end_dt.isoformat(), "timeZone": "UTC"}

            updated = service.events().patch(calendarId="primary", eventId=event_id, body=patch).execute()
            return {"status": "success", "message": "Event updated successfully", "data": {"event_id": updated.get("id")}}

        if action == "cancel_event":
            event_id = payload.get("event_id")
            if not event_id:
                return {"status": "error", "message": "event_id is required for cancel_event"}
            service.events().delete(calendarId="primary", eventId=event_id).execute()
            return {"status": "success", "message": "Event cancelled successfully", "data": {"event_id": event_id}}
        if action == "list_events":
            start_date = payload.get("start_date")
            end_date = payload.get("end_date")
            candidate_name = (payload.get("candidate_name") or "").strip().lower()

            kwargs = {
                "calendarId": "primary",
                "maxResults": 100,
                "singleEvents": True,
                "orderBy": "startTime"
            }
            if start_date:
                kwargs["timeMin"] = start_date if ("Z" in start_date or "+" in start_date) else start_date + "T00:00:00Z"
            else:
                now = datetime.datetime.utcnow()
                kwargs["timeMin"] = now.isoformat() + "Z"

            if end_date:
                kwargs["timeMax"] = end_date if ("Z" in end_date or "+" in end_date) else end_date + "T23:59:59Z"

            events_result = service.events().list(**kwargs).execute()
            items = events_result.get("items", [])

            normalized_events = []
            for item in items:
                summary = item.get("summary", "")
                description = item.get("description", "")
                attendees = [a.get("email") for a in item.get("attendees", []) if a.get("email")]

                candidate = ""
                summary_lower = summary.lower()
                if "interview with " in summary_lower:
                    candidate = summary[summary_lower.find("interview with ") + 15:].strip()
                elif " interview" in summary_lower:
                    candidate = summary[:summary_lower.find(" interview")].strip()
                else:
                    for att in attendees:
                        if "example.com" not in att and "praje" not in att:
                            candidate = att.split("@")[0].title()
                            break
                    if not candidate and attendees:
                        candidate = attendees[0].split("@")[0].title()

                if candidate_name:
                    text_to_search = f"{summary} {description} {candidate}".lower()
                    if candidate_name not in text_to_search:
                        continue

                normalized_events.append({
                    "id": item.get("id"),
                    "title": summary,
                    "candidate": candidate,
                    "start_time": item.get("start", {}).get("dateTime") or item.get("start", {}).get("date"),
                    "end_time": item.get("end", {}).get("dateTime") or item.get("end", {}).get("date"),
                    "meeting_link": item.get("hangoutLink", ""),
                    "attendees": attendees
                })

            return {
                "status": "success",
                "events": normalized_events
            }

        if action == "get_dashboard_metrics":
            # For hackathon purposes, fetch upcoming events and count
            now = datetime.datetime.utcnow().isoformat() + "Z"
            events_result = service.events().list(
                calendarId="primary",
                timeMin=now,
                maxResults=100,
                singleEvents=True,
                orderBy="startTime"
            ).execute()
            events = events_result.get("items", [])
            
            upcoming_interviews_count = len(events)
            next_interview = events[0].get("summary") if events else "None scheduled"
            next_interview_time = events[0].get("start", {}).get("dateTime") if events else None
            
            # Format time if exists
            if next_interview_time:
                try:
                    dt = datetime.datetime.fromisoformat(next_interview_time.replace("Z", "+00:00"))
                    next_interview_time = dt.strftime("%b %d, %I:%M %p")
                except:
                    pass

            return {
                "status": "success",
                "data": {
                    "calendar": {
                        "upcoming_interviews_count": upcoming_interviews_count,
                        "next_interview": next_interview,
                        "next_interview_time": next_interview_time
                    }
                }
            }

        return {"status": "error", "message": f"Unknown action: {action}"}

    except Exception as e:
        return {"status": "error", "message": f"Calendar API Error: {str(e)}"}
