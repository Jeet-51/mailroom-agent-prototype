# agents/extractor.py
#
# Architecture:
#   This is the Extractor Agent. It uses two Tools:
#     - classify_deadline_type(): determines Explicit / Conditional / Implicit
#     - calculate_due_date():     computes the actual deadline date using legal rules
#
#   These tools are called by the agent and their results are fed back into
#   the final extraction prompt — demonstrating the Skills + Agents + Tools pattern.

import json
import os
from datetime import datetime, timedelta
from anthropic import AsyncAnthropic


# ─── LEGAL SKILL ────────────────────────────────────────────────────────────

def load_claude_md() -> str:
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(root, "CLAUDE.md")
    if os.path.exists(path):
        with open(path, "r") as f:
            return f.read()
    return "You are a legal mailroom extractor agent. Always respond with valid JSON only."


# ─── TOOL 1: classify_deadline_type ─────────────────────────────────────────

def classify_deadline_type(email_body: str, email_subject: str) -> dict:
    """
    Tool: Classify whether a deadline is Explicit, Conditional, or Implicit.

    Rules applied:
    - Explicit: a specific date or "by [date]" phrase is present
    - Conditional: deadline is triggered by an event ("once you receive", "upon service")
    - Implicit: deadline must be inferred (offer expiration, SOL, court motion rules)
    """
    text = (email_subject + " " + email_body).lower()

    # Explicit signals
    explicit_signals = [
        "by december", "by january", "by february", "by march", "by april",
        "by may", "by june", "by july", "by august", "by september",
        "by october", "by november", "must be filed by", "due by",
        "deadline is", "no later than", "respond by", "due on",
        "submit by", "file by", "scheduled for"
    ]

    # Conditional signals
    conditional_signals = [
        "once you receive", "upon receipt", "after you receive",
        "when you get", "upon service", "once served", "clock starts",
        "window begins", "upon delivery", "after receiving"
    ]

    # Implicit signals
    implicit_signals = [
        "valid for", "expires in", "kindly reply within", "reply within",
        "within 10 days", "within 15 days", "within 30 days",
        "motion for summary judgment", "motion to dismiss", "motion filed",
        "surgery", "accident occurred", "injury occurred", "malpractice",
        "statute of limitations", "filed by defendant", "filed by plaintiff"
    ]

    explicit_score = sum(1 for s in explicit_signals if s in text)
    conditional_score = sum(1 for s in conditional_signals if s in text)
    implicit_score = sum(1 for s in implicit_signals if s in text)

    if conditional_score > 0:
        deadline_type = "Conditional"
        confidence = "high" if conditional_score >= 2 else "medium"
    elif explicit_score > 0:
        deadline_type = "Explicit"
        confidence = "high" if explicit_score >= 2 else "medium"
    elif implicit_score > 0:
        deadline_type = "Implicit"
        confidence = "medium"
    else:
        deadline_type = "Implicit"
        confidence = "low"

    return {
        "deadline_type": deadline_type,
        "confidence": confidence,
        "explicit_score": explicit_score,
        "conditional_score": conditional_score,
        "implicit_score": implicit_score
    }


# ─── TOOL 2: calculate_due_date ─────────────────────────────────────────────

def calculate_due_date(
    deadline_type: str,
    email_date: str,
    days_mentioned: int = None,
    event_date: str = None,
    sol_years: int = None,
    motion_type: str = None
) -> dict:
    """
    Tool: Calculate the actual due date based on deadline type and legal rules.

    - Explicit: returned as-is from AI extraction (this tool confirms it's parseable)
    - Conditional: returns null (clock hasn't started)
    - Implicit: calculates from email_date + days, or event_date + SOL, or motion rules
    """
    try:
        base_date = datetime.strptime(email_date, "%Y-%m-%d")
    except Exception:
        base_date = datetime.now()

    if deadline_type == "Conditional":
        return {
            "due_date": None,
            "reasoning": "Conditional deadline — clock starts when trigger event occurs. Set a reminder."
        }

    if deadline_type == "Implicit":
        # Offer/response expiration
        if days_mentioned:
            due = base_date + timedelta(days=days_mentioned)
            return {
                "due_date": due.strftime("%Y-%m-%d"),
                "reasoning": f"Calculated from email date ({email_date}) + {days_mentioned} days"
            }

        # Statute of limitations
        if sol_years and event_date:
            try:
                event_dt = datetime.strptime(event_date, "%Y-%m-%d")
                due = event_dt.replace(year=event_dt.year + sol_years)
                return {
                    "due_date": due.strftime("%Y-%m-%d"),
                    "reasoning": f"{sol_years}-year statute of limitations from event date {event_date}"
                }
            except Exception:
                pass

        # Motion response deadlines (federal default: 21 days)
        if motion_type:
            due = base_date + timedelta(days=21)
            return {
                "due_date": due.strftime("%Y-%m-%d"),
                "reasoning": f"Opposition to {motion_type} due in 21 days per FRCP (from {email_date})"
            }

        return {"due_date": None, "reasoning": "Implicit deadline — could not calculate automatically"}

    # Explicit: AI will extract the date, this tool just confirms the logic
    return {"due_date": None, "reasoning": "Explicit date to be extracted directly from email text"}


# ─── EXTRACTOR AGENT ────────────────────────────────────────────────────────

async def extract_from_email(email: dict) -> dict:
    """
    Extractor Agent pipeline:
      1. Call Tool: classify_deadline_type  → determines type
      2. Call Tool: calculate_due_date      → computes date for implicit/conditional
      3. Call Claude Agent                  → full extraction with tool hints injected
    """

    # Step 1 — Tool: classify deadline type
    classification = classify_deadline_type(
        email_body=email.get("body", ""),
        email_subject=email.get("subject", "")
    )

    # Step 2 — Tool: calculate due date (for implicit deadlines)
    date_hint = calculate_due_date(
        deadline_type=classification["deadline_type"],
        email_date=email.get("date", datetime.now().strftime("%Y-%m-%d")),
    )

    # Step 3 — Claude Agent with tool results injected into prompt
    prompt = f"""
You are a legal mailroom Extractor Agent. Analyze this email and return structured JSON.

Email:
ID: {email['id']}
From: {email['from']}
Subject: {email['subject']}
Date: {email['date']}
Body: {email['body']}

Tool Results (already computed — use these to inform your response):
- classify_deadline_type() returned: {json.dumps(classification)}
- calculate_due_date() returned: {json.dumps(date_hint)}

Using the tool results above and the legal knowledge in your system prompt, return ONLY this JSON:
{{
    "email_id": "{email['id']}",
    "use_case": "Expert Disclosure | Medical Records | Settlement Offer | Deposition | Malpractice | Motion Response | Other",
    "deadline_type": "{classification['deadline_type']}",
    "due_date": "YYYY-MM-DD extracted from email text, or use tool-calculated date, or null",
    "urgency": "HIGH | MEDIUM | LOW",
    "todo_action": "verb-first, include party/case name, max 8 words (e.g. 'File MSJ opposition — Davis v. City', 'Review settlement offer — Thompson', 'Obtain HIPAA auth — Johnson case')",
    "summary": "one sentence summary of why this email matters",
    "assigned_to": "attorney name if mentioned else null",
    "implicit_reasoning": "for Implicit type only: which legal rule was applied (SOL, court rule, expiration math)"
}}

For Explicit deadlines: extract the exact date stated in the email.
For Conditional deadlines: due_date must be null.
For Implicit deadlines: use the tool-calculated date if available, otherwise reason from legal rules.
"""

    client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    response = await client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=load_claude_md(),
        messages=[{"role": "user", "content": prompt}],
    )

    full_response = response.content[0].text if response.content else ""

    try:
        clean = full_response.strip()
        if "```json" in clean:
            clean = clean.split("```json")[1].split("```")[0].strip()
        elif "```" in clean:
            clean = clean.split("```")[1].split("```")[0].strip()
        return json.loads(clean)
    except Exception as e:
        return {
            "email_id": email["id"],
            "error": f"Parse failed: {str(e)}",
            "raw_response": full_response
        }
