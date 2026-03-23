"""
Run this ONCE before starting the server to authenticate Gmail.
After this completes, token.json is saved and the server never prompts again.

Usage:
    uv run python auth_gmail.py
"""
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
flow.redirect_uri = 'http://localhost'
auth_url, _ = flow.authorization_url(prompt='consent')

print("\n" + "="*60)
print("  GMAIL ONE-TIME SETUP")
print("="*60)
print("\nStep 1 — Open this URL in your browser:\n")
print(auth_url)
print("\nStep 2 — Sign in with jp8511749@gmail.com and allow access.")
print("Step 3 — Browser shows 'This site can't be reached' — that's OK.")
print("Step 4 — Copy the FULL URL from address bar and paste below.")
print("="*60 + "\n")

redirect_response = input("Paste the full redirect URL here: ").strip()
flow.fetch_token(authorization_response=redirect_response)
creds = flow.credentials

with open('token.json', 'w') as f:
    f.write(creds.to_json())

# Quick test
service = build('gmail', 'v1', credentials=creds)
profile = service.users().getProfile(userId='me').execute()
print(f"\n✅ Auth complete! Connected as: {profile['emailAddress']}")
print("token.json saved — the server will use it automatically from now on.\n")
