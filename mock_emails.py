MOCK_EMAILS = [
    # ── 001 Explicit — Expert Disclosure hard date ────────────────────────────
    {
        "id": "email_001",
        "from": "opposing.counsel@lawfirm.com",
        "to": "michael@ourfirm.com",
        "subject": "Expert Disclosures Due December 1st - Johnson v. MedCorp",
        "date": "2025-11-24",
        "body": """
Dear Michael,

As per the scheduling order in Johnson v. MedCorp (Case No. 2024-CV-4821),
all expert disclosures must be filed with the court by December 1st, 2025.

Please ensure your expert witness list and supporting documentation
are submitted no later than 5:00 PM EST on that date.

Failure to comply may result in exclusion of expert testimony at trial.

Regards,
Sarah Chen
Opposing Counsel
"""
    },

    # ── 002 Conditional — Medical records 30-day discovery clock ─────────────
    {
        "id": "email_002",
        "from": "records@stmaryhospital.org",
        "to": "becky@ourfirm.com",
        "subject": "Medical Records Request - Martinez Case",
        "date": "2025-11-24",
        "body": """
Dear Becky,

We have received your HIPAA authorization for patient Carlos Martinez.

Please note that once you receive the requested medical records,
your 30-day window to respond to the defendant's discovery request
will begin immediately.

We anticipate processing your records request within 5-7 business days.

Best regards,
St. Mary's Hospital Records Department
"""
    },

    # ── 003 Implicit — Settlement offer expiration math ───────────────────────
    {
        "id": "email_003",
        "from": "defense.counsel@biglaw.com",
        "to": "white@ourfirm.com",
        "subject": "Settlement Offer - Thompson v. Insurance Co.",
        "date": "2025-11-24",
        "body": """
Dear Counsel,

On behalf of our client, we are pleased to extend a settlement offer
of $75,000 in full resolution of the above-referenced matter.

This offer is valid for 30 days from the date of this letter.
After this period, the offer will be automatically withdrawn.

Please discuss with your client and respond at your earliest convenience.

Regards,
James Porter
Defense Counsel
"""
    },

    # ── 004 Implicit — Motion for Summary Judgment (21-day court rule) ────────
    {
        "id": "email_004",
        "from": "notifications@courts.gov",
        "to": "counsel@ourfirm.com",
        "subject": "Motion for Summary Judgment Filed - Davis v. City",
        "date": "2026-03-23",
        "body": """
Dear Counsel,

Please be advised that the defendant has filed a Motion for Summary Judgment
in Davis v. City (Case No. 2024-CV-9012).

Under local court rules, your opposition is due within 21 days of this filing.

Regards,
Court Notification System
"""
    },

    # ── 005 Explicit — HIPAA authorization hard deadline ─────────────────────
    {
        "id": "email_005",
        "from": "records@generalmedical.org",
        "to": "becky@ourfirm.com",
        "subject": "HIPAA Authorization Required - Johnson Case - Respond by April 1",
        "date": "2026-03-23",
        "body": """
Dear Becky,

We are in receipt of your medical records request for patient Linda Johnson.

Before we can release any records, we require a signed HIPAA authorization
form from the patient. Please provide the completed authorization no later
than April 1, 2026.

If we do not receive the authorization by this date, your request will be
closed and you will need to resubmit.

Best regards,
General Medical Center Records Department
"""
    },

    # ── 006 Implicit — Medical malpractice SOL (surgery date + 2 years) ──────
    {
        "id": "email_006",
        "from": "intake@ourfirm.com",
        "to": "partner@ourfirm.com",
        "subject": "New Client Intake - Medical Malpractice - Rivera",
        "date": "2026-03-23",
        "body": """
Hi,

New client walked in today regarding a potential medical malpractice claim.

Patient: Maria Rivera
Incident: Surgical error during routine appendectomy at General Hospital.
Date of Surgery: March 3, 2024

The surgeon accidentally nicked the bowel, leading to severe infection
and extended hospitalization. Client has not filed any legal action yet.

Please advise on next steps and whether we are taking this case.

Thanks,
Intake Team
"""
    },
]
