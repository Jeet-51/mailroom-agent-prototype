# Legal Mailroom Agent

AI-powered legal email processor for personal injury law firms. Reads emails, extracts deadlines, classifies urgency, and creates prioritized to-dos.

Built with: Claude API, FastAPI, Gmail API, Anthropic SDK

---

## The Problem

Legal teams get dozens of emails a day. Buried inside them are deadlines that cause malpractice if missed. A motion filed by opposing counsel triggers a 21-day response window. A surgery date starts a 2-year statute of limitations clock. A settlement offer expires in 30 days. None of these show up as calendar invites. They live in email text.

---

## How It Works

```
Gmail / Demo Emails
        |
  Pre-filter Layer
  (spam blocked before any API call)
        |
  Extractor Agent  <-- Tool 1: classify_deadline_type()
  (1 Claude call        Tool 2: calculate_due_date()
   per email)
        |
  Action Agent
  (deterministic, no API cost)
        |
  Prioritized To-Do List
  Act Today / This Week / Monitor
```

### Three Deadline Types

| Type | Example | How it works |
|---|---|---|
| Explicit | "File by December 1st" | Pulls the stated date directly |
| Conditional | "30-day clock starts on receipt of records" | Detects the trigger event, sets a reminder |
| Implicit | No date in email | Applies legal rules: 21-day MSJ window, 2-year malpractice SOL |

Implicit is the hardest and most valuable. It needs legal domain knowledge, not just date parsing.

---

## Agent Architecture

### Skill
Legal domain knowledge lives in `CLAUDE.md` and is injected into every agent call as a system prompt. It contains PI statute of limitations rules, FRCP motion deadlines, discovery windows, and settlement expiration logic. This is the shared brain across all agents.

### Tools (local, zero API cost)
Two tools run before any Claude call:

- `classify_deadline_type()` scans the email for explicit, conditional, and implicit signals and returns a confidence-scored classification
- `calculate_due_date()` computes the actual deadline using legal rules: adds days to the email date for expiration cases, calculates SOL from event dates, applies the 21-day motion response rule

The tool results are injected directly into the Claude prompt, so the model reasons on pre-computed structure rather than raw text alone.

### Extractor Agent
Takes one email, runs both tools, then makes a single Claude API call with the tool output baked into the prompt. Returns structured JSON with deadline type, due date, urgency, case summary, and implicit reasoning. This is the only step that calls the API.

### Action Agent
Takes the Extractor output and assigns priority (Act Today / This Week / Monitor) and action steps using a deterministic lookup table keyed by use case. No API call. Consistent, fast, and free.

### Orchestrator
Runs Extractor and Action agents across all emails in parallel using `asyncio.gather`. Includes a pre-filter that blocks obvious spam before touching Claude, an email ID cache to skip already-processed messages, and thread deduplication to prevent duplicates from forwarded emails.

---

## Screenshots

### Demo Mode - All 6 Legal Use Cases

| Email | Use Case | Deadline Type |
|---|---|---|
| Expert disclosures, Johnson v. MedCorp | Filing deadline | Explicit |
| Medical records, Martinez case | Discovery window | Conditional |
| Settlement offer, Thompson | Offer expiration | Implicit |
| Motion for Summary Judgment, Davis v. City | 21-day court rule | Implicit |
| HIPAA authorization, Johnson case | Hard deadline | Explicit |
| Malpractice intake, Rivera | 2-year SOL | Implicit |

<img width="1881" height="935" alt="image" src="https://github.com/user-attachments/assets/abb1201f-46b8-4d1c-bfe5-0f531e6ebaa5" />

![Mock Emails Demo](<img width="1881" height="935" alt="image" src="https://github.com/user-attachments/assets/a154bef1-2404-41a2-bd04-9eabbe748a9b" />)

Act Today 6, 6 HIGH urgency. All 6 flagged correctly.

The Rivera case is the clearest example of implicit reasoning. Surgery date was March 3, 2024. No deadline is mentioned anywhere in the email. The agent calculated the 2-year statute of limitations expiry on its own and flagged it as Act Today.

---

### Real Gmail - Live Inbox
![image.png](attachment:f730bd37-30a3-4058-a2a0-d1e562762184:image.png)
![Real Gmail Demo](screenshots/real_gmail.png)

Gmail OAuth connected. Agent fetched the real inbox, filtered marketing emails into Monitor, and surfaced Act Today items including the Motion for Summary Judgment with FRCP Rule 56 reasoning and the 21-day calculation shown inline.

Connect your Gmail account via OAuth and the agent fetches emails from the last 1-24 hours, filters spam locally before any API call, and only sends legal emails through Claude. Already-processed emails are cached by message ID so repeat runs skip them instantly.

---

### Legal Rule Applied

When an implicit deadline is detected, the agent shows its reasoning:

Settlement offer:
> "Email states valid for 30 days from the date of this letter (2026-03-23). Expiration calculated as 2026-03-23 + 30 days = 2026-04-22. HIGH urgency because missing this deadline forecloses settlement negotiations and may expose the client to continued litigation costs."

MSJ opposition:
> "Federal Rule of Civil Procedure 56 and local court rules set a 21-day response deadline from the motion filing date. Email dated 2026-03-23, adding 21 days = 2026-04-13. Court deadline with irreversible consequences if missed."

---

## Tech Stack

| Component | Technology |
|---|---|
| Backend | FastAPI (Python) |
| AI | Anthropic Claude API (claude-haiku-4-5) |
| Gmail | Google Gmail API + OAuth 2.0 |
| Frontend | Vanilla JS + CSS |
| Async | asyncio.gather for parallel processing |

---

## Tradeoffs

| Decision | Options | What I chose | Why |
|---|---|---|---|
| Agent design | Single agent does everything vs separate agents per role | Two agents: Extractor + Action | Separation of concerns — each agent has one job and can be tested, swapped, or scaled independently |
| Action Agent | AI generates priority and steps vs deterministic lookup table | Deterministic lookup table | AI is inconsistent on repetitive classification tasks. Rules are faster, cheaper, and more predictable. AI only where language understanding is actually needed |
| Pre-filter | Block emails missing legal keywords vs block only confirmed spam | Block only confirmed spam | Missing a real legal deadline is malpractice. Better to send one extra email to Claude than to silently drop something important |
| Processing | Sequential email processing vs parallel | Parallel with asyncio.gather | A legal team gets many emails at once. Sequential processing would make the tool too slow to be useful in practice |

Roughly $0.01 per run for 6 emails. Email ID cache skips already-processed messages on repeat runs.

---

## Running Locally

```bash
uv sync

# add to .env
ANTHROPIC_API_KEY=sk-ant-...

uv run uvicorn main:app --reload --port 8000
```

Open localhost:8000 and click Run Agent. No login needed for Demo Mode.

For real Gmail: click Real Gmail, then Connect Gmail, authenticate, then Run Agent.

---

## Planned Features

- PDF attachments: if an email contains a legal PDF (court filing, medical record, demand letter), the Extractor Agent will parse the attachment and include a summary in the to-do alongside the deadline
- Chrome extension: run the agent directly inside Gmail as a sidebar, no separate app needed
- Execution Agent: autonomously drafts response emails, opposition briefs, and scheduling requests based on the to-do. Attorney reviews the draft and clicks send. Human approval is required before anything goes out, which matters when working with high-stakes legal decisions
- Multi-user support: each firm gets its own OAuth token and isolated inbox processing

Gmail OAuth is currently in test mode. Production deployment requires Google's OAuth verification process, which is standard for any app requesting Gmail access.
