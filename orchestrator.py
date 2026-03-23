# orchestrator.py
import asyncio
import os
import json
from dotenv import load_dotenv
from mock_emails import MOCK_EMAILS
from agents.extractor import extract_from_email
from agents.action import create_todo

load_dotenv()

# ─── IN-MEMORY EMAIL CACHE ───────────────────────────────────────────────────
# Persists for the server session. Prevents reprocessing emails on every run.
# In production: replace with Redis or a database.

_processed_ids: set = set()

def is_processed(email_id: str) -> bool:
    return email_id in _processed_ids

def mark_processed(email_id: str):
    _processed_ids.add(email_id)

def clear_cache():
    """Call this if you want to force reprocess all emails."""
    _processed_ids.clear()


# ─── PRE-FILTER ──────────────────────────────────────────────────────────────
# Keyword check before ANY Claude API call.
# Saves cost by skipping obvious spam / non-legal emails instantly.

# ── Layer 2: Legal domains (checked FIRST — always pass, never blocked) ──────
LEGAL_DOMAINS = [
    ".gov", "court.", "courts.", "judiciary",
    "law.com", "legalmail", "attorney", "counsel", "esq.",
]

# ── Layer 1: Airtight spam signals (NEVER appear in real legal emails) ────────
# Words like "offer", "expires", "respond" are NOT here — settlement emails use them
SPAM_SIGNALS = [
    "unsubscribe",
    "referral reward",
    "buy now",
    "free trial",
    "sale ends",
    "click here to claim",
    "webinar registration",
    "grocery",
    "promo code",
    "limited time offer",
    "vip membership",
    "job alert",
    "recruitment",
    "you've been selected",
    "congratulations you won",
    "earn rewards",
]


def is_legal_email(email: dict) -> bool:
    """
    Two-layer pre-filter. Zero API calls.

    Layer 2 (runs first): known legal domain → always pass, cannot be blocked
    Layer 1 (runs second): 2+ airtight spam signals → block
    Everything else → pass to Claude to decide
    """
    from_addr = email.get("from", "").lower()
    subject   = email.get("subject", "").lower()
    body      = email.get("body", "")[:800].lower()
    text      = subject + " " + body

    # ── Layer 2: legal domain always wins ────────────────────────────────────
    if any(d in from_addr for d in LEGAL_DOMAINS):
        return True

    # ── Layer 1: only block on airtight spam signals ──────────────────────────
    spam_hits = sum(1 for s in SPAM_SIGNALS if s in text)
    if spam_hits >= 2:
        return False

    # ── Default: send to Claude — it decides ─────────────────────────────────
    return True


# ─── GMAIL FETCH ─────────────────────────────────────────────────────────────

async def fetch_gmail_emails(hours: int = 4) -> list:
    try:
        from gmail_client import fetch_recent_emails
        emails = await asyncio.to_thread(fetch_recent_emails, hours)
        if not emails:
            print(f"No emails found in last {hours} hours. Using mock emails.")
            return MOCK_EMAILS
        return emails
    except Exception as e:
        print(f"Gmail fetch failed: {e}. Falling back to mock emails.")
        return MOCK_EMAILS


# ─── MAIN PIPELINE ───────────────────────────────────────────────────────────

async def run_pipeline(use_gmail: bool = False, hours: int = 4) -> list:
    """
    Pipeline:
    1. Fetch emails (Gmail or mock)
    2. Pre-filter — skip non-legal emails (zero API cost)
    3. Cache check — skip already-processed email IDs
    4. Extractor Agent — ONE Claude call per email (classify + extract)
    5. Action Agent  — deterministic, zero Claude calls
    """
    print("Starting Mailroom Agent Pipeline...")

    if use_gmail:
        print(f"Fetching emails from last {hours} hours...")
        emails = await fetch_gmail_emails(hours=hours)
    else:
        print("Using mock emails...")
        emails = MOCK_EMAILS

    total = len(emails)

    # Step 2: Pre-filter
    legal_emails = [e for e in emails if is_legal_email(e)]
    skipped_spam = total - len(legal_emails)
    print(f"Pre-filter: {len(legal_emails)} legal / {skipped_spam} skipped (non-legal)")

    # Step 3: Cache check
    new_emails = [e for e in legal_emails if not is_processed(e["id"])]
    cached_count = len(legal_emails) - len(new_emails)
    print(f"Cache: {len(new_emails)} new / {cached_count} already processed")

    if not new_emails:
        print("All emails already processed. Returning cached results.")
        # Return empty — UI shows "no new emails"
        return []

    # Step 4: Extractor Agent (parallel)
    print(f"Extractor Agent: processing {len(new_emails)} emails in parallel...")
    extracted_list = await asyncio.gather(
        *[extract_from_email(email) for email in new_emails]
    )

    # Step 5: Action Agent (deterministic, no API calls)
    print("Action Agent: assigning priorities and action steps...")
    todos = [create_todo(extracted) for extracted in extracted_list]

    # Mark all as processed
    for email in new_emails:
        mark_processed(email["id"])

    print(f"Pipeline complete. {len(todos)} to-dos created.")
    print(f"API calls made: {len(new_emails)} (1 per new legal email)")
    return todos


if __name__ == "__main__":
    todos = asyncio.run(run_pipeline(use_gmail=False))
    print(json.dumps(todos, indent=2))
