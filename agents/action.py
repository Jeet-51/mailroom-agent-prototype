# agents/action.py
#
# Architecture:
#   This is the Action Agent. It is DETERMINISTIC — no LLM call needed.
#   It applies a legal knowledge lookup table (Skill) to assign:
#     - Priority:     Act Today / This Week / Monitor
#     - Action Steps: pre-defined playbook per use case
#
#   This design choice is intentional:
#     "Not every agent needs AI. Deterministic agents are faster, cheaper,
#      and more predictable for rule-based tasks like priority assignment."
#

# ─── ACTION STEPS SKILL ─────────────────────────────────────────────────────
# Pre-defined playbooks per legal use case (PI / mass tort focused)

ACTION_PLAYBOOK = {
    "Expert Disclosure": [
        "Verify expert witness has been retained and briefed on case facts",
        "Confirm expert report is on track for the filing deadline",
        "File expert disclosures with the court by the stated deadline",
        "Serve opposing counsel copies immediately after filing",
    ],
    "Medical Records": [
        "Contact records department to confirm current status of records request",
        "Log exact receipt date when records arrive — starts the 30-day clock",
        "Assign paralegal to review, organize, and Bates-stamp records",
        "Schedule attorney review session to assess case value impact",
    ],
    "Settlement Offer": [
        "Pull case economics: calculate net recovery after fees, liens, and costs",
        "Schedule client consultation call within 48 hours to present the offer",
        "Prepare written acceptance, rejection, or counter-offer letter",
        "Submit formal response before the offer expiration deadline",
    ],
    "Motion Response": [
        "Pull the filed motion and all supporting documentation immediately",
        "Research applicable case law and identify genuine disputes of material fact",
        "Draft opposition brief with legal arguments and supporting exhibits",
        "File opposition brief before the 21-day FRCP deadline",
    ],
    "Deposition": [
        "Confirm deposition date, time, location, and court reporter with all parties",
        "Conduct witness prep session — review likely questions and exhibits",
        "Organize and produce any documents required before the deposition",
        "Arrange video recording if needed for trial preservation",
    ],
    "Malpractice": [
        "Calculate the exact statute of limitations deadline from the incident date",
        "Gather all medical records, treatment history, and billing documentation",
        "Retain a qualified medical expert to assess standard of care deviation",
        "File complaint before SOL expires — failure is irreversible malpractice",
    ],
    "HIPAA Authorization": [
        "Contact client immediately to explain HIPAA authorization requirement",
        "Send authorization form for wet or electronic signature",
        "Submit signed authorization to the requesting party",
        "Confirm receipt and log in case management system",
    ],
    "Document Production": [
        "Identify all documents responsive to the production request",
        "Apply privilege review — log any withheld documents on privilege log",
        "Produce documents in the required format by the stated deadline",
        "Serve opposing counsel with production and cover letter",
    ],
    "Other": [
        "Review email and classify the legal matter type",
        "Assign to the appropriate attorney or paralegal",
        "Set a follow-up reminder for 2 business days",
    ],
}


# ─── PRIORITY ASSIGNMENT SKILL ───────────────────────────────────────────────

def assign_priority(urgency: str, deadline_type: str, due_date) -> str:
    """
    Deterministic priority assignment — no LLM needed.
    Rules:
      - HIGH urgency           → Act Today
      - MEDIUM urgency         → This Week
      - LOW + Explicit date    → This Week (has a real deadline)
      - LOW + no date          → Monitor
    """
    if urgency == "HIGH":
        return "Act Today"
    if urgency == "MEDIUM":
        return "This Week"
    # LOW urgency
    if due_date and due_date not in ("null", "None", ""):
        return "This Week"
    return "Monitor"


# ─── ACTION AGENT ────────────────────────────────────────────────────────────

def create_todo(extracted: dict) -> dict:
    """
    Action Agent: converts extractor output into a structured to-do.
    Pure Python — zero API calls, instant, deterministic.
    """
    if "error" in extracted:
        return {
            "email_id": extracted.get("email_id"),
            "error": extracted["error"],
        }

    use_case  = extracted.get("use_case", "Other")
    urgency   = extracted.get("urgency", "LOW")
    due_date  = extracted.get("due_date")
    deadline_type = extracted.get("deadline_type", "Implicit")

    steps = ACTION_PLAYBOOK.get(use_case, ACTION_PLAYBOOK["Other"])

    return {
        "email_id":          extracted.get("email_id"),
        "todo_title":        extracted.get("todo_action", "Review email"),
        "priority":          assign_priority(urgency, deadline_type, due_date),
        "deadline_type":     deadline_type,
        "due_date":          due_date,
        "urgency":           urgency,
        "action_steps":      steps,
        "assigned_to":       extracted.get("assigned_to"),
        "summary":           extracted.get("summary", ""),
        "use_case":          use_case,
        "implicit_reasoning": extracted.get("implicit_reasoning"),
        "subject":           extracted.get("subject", ""),
    }
