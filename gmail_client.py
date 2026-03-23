# gmail_client.py
# Direct Gmail API client - faster than Composio MCP

import os
import base64
import json
from datetime import datetime, timedelta

# Required for local OAuth over http (dev only)
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def get_gmail_service():
    """Authenticate and return Gmail service."""
    creds = None

    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open('token.json', 'w') as f:
                f.write(creds.to_json())
        else:
            raise RuntimeError(
                "Gmail not authenticated. Run 'uv run python auth_gmail.py' first."
            )

    return build('gmail', 'v1', credentials=creds)


def get_email_body(payload):
    """Extract plain text body from email payload."""
    body = ""

    if 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/plain':
                data = part['body'].get('data', '')
                if data:
                    body = base64.urlsafe_b64decode(data).decode('utf-8')
                    break
            elif 'parts' in part:
                body = get_email_body(part)
                if body:
                    break
    else:
        data = payload.get('body', {}).get('data', '')
        if data:
            body = base64.urlsafe_b64decode(data).decode('utf-8')

    return body


def fetch_recent_emails(hours: int = 4) -> list:
    """
    Fetch emails from last N hours directly via Gmail API.
    Returns list of email dicts matching our standard format.
    """
    service = get_gmail_service()

    # Build time filter
    since = datetime.utcnow() - timedelta(hours=hours)
    since_timestamp = int(since.timestamp())

    query = f"after:{since_timestamp}"

    results = service.users().messages().list(
        userId='me',
        q=query,
        maxResults=10
    ).execute()

    messages = results.get('messages', [])

    if not messages:
        return []

    emails = []
    seen_threads = set()
    seen_subjects = set()
    for msg in messages:
        # Deduplicate by thread
        thread_id = msg.get('threadId', msg['id'])
        if thread_id in seen_threads:
            continue
        seen_threads.add(thread_id)

        msg_data = service.users().messages().get(
            userId='me',
            id=msg['id'],
            format='full'
        ).execute()

        headers = {h['name']: h['value']
                   for h in msg_data['payload']['headers']}

        body = get_email_body(msg_data['payload'])

        # Get date
        date_str = headers.get('Date', '')
        try:
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(date_str)
            date_formatted = dt.strftime('%Y-%m-%d')
        except:
            date_formatted = datetime.utcnow().strftime('%Y-%m-%d')

        # Deduplicate by normalized subject (catches Fwd:/Re: copies)
        raw_subject = headers.get('Subject', '')
        normalized = raw_subject.lower().replace('fwd:', '').replace('re:', '').strip()
        if normalized in seen_subjects:
            continue
        seen_subjects.add(normalized)

        emails.append({
            "id": msg['id'],
            "from": headers.get('From', ''),
            "to": headers.get('To', ''),
            "subject": headers.get('Subject', ''),
            "date": date_formatted,
            "body": body
        })

    return emails
