---
description: Triage Gmail inbox — fetch threads, categorize noise vs. actionable, bulk delete/archive noise, convert actionables to TickTick tasks, use /walkthrough for per-item decisions on ambiguous items. Use when the user says "check my inbox", "clean up my inbox", "triage inbox", "inbox zero", or invokes /email-inbox.
argument-hint: "[--page N] [--auto] [--no-tasks]"
---

# Email Inbox Triage

Fetch Gmail inbox, triage into noise vs. actionable, clean up noise in bulk,
convert actionables to TickTick tasks, use /walkthrough for ambiguous items.

**Flags:**
- `--page N` — start at page N (each page = 50 threads); default starts at page 1
- `--auto` — skip per-item walkthrough, apply recommended actions automatically
- `--no-tasks` — triage only, don't create TickTick tasks

## Step 1 — Fetch inbox

Fetch up to 50 threads:

```
search_threads(query="in:inbox", pageSize=50)
```

If inbox is empty: report inbox zero and exit.

Track `nextPageToken` — offer to continue to next page after each batch.

## Step 2 — Categorize threads

Sort every thread into one of four buckets:

### NOISE (safe to bulk-delete or bulk-archive)
- Shipped / delivered / out-for-delivery notifications (already done)
- Past-event reminders (appointments, school digests, past deadlines)
- Promotional / marketing emails
- Newsletters (unless user has expressed interest)
- Duplicate automated alerts (ecobee, Quicken, PayPal login, etc.)
- Expired offers or notices
- Auth confirmations already acted on (login links, device notices)

### ARCHIVE (keep searchable, remove from inbox)
- Purchase receipts / license keys / activation codes (reference value)
- Financial statements (Schwab, USAA, Citi, PayPal)
- Account welcome / setup emails

### ACTIONABLE (needs human decision)
- Unpaid invoices or bills due
- Tasks or portal items assigned to user
- Pending payments or orders awaiting payment
- Expiring tokens, credentials, registrations
- Recruiter / job outreach (user decides interest)
- Family / personal threads needing reply
- Starred items
- Security alerts that may need investigation

### AMBIGUOUS (unclear — flag for walkthrough)
- Anything that doesn't fit cleanly above
- Items where context would change the action

## Step 3 — Present triage summary

Show a compact table:

```
INBOX TRIAGE — Page N — {count} threads

ACTIONABLE ({n})
  - [description] — [sender] — [date]
  ...

AMBIGUOUS ({n})
  - [description] — [sender] — [date]
  ...

NOISE — {n} threads (bulk delete)
ARCHIVE — {n} threads (bulk archive)
```

Ask how to handle noise/archive batches:
- Offer "delete all noise / archive all archive-worthy / walk through ambiguous"
- If `--auto`: apply immediately without asking

## Step 4 — Handle noise + archive batches

For NOISE threads: `label_thread(threadId, ["TRASH"])` for each.
For ARCHIVE threads: `unlabel_thread(threadId, ["INBOX"])` for each.

Run in parallel batches of 10.

## Step 5 — Walk through AMBIGUOUS items

Use the /walkthrough pattern: one item at a time, offer:
1. Keep in inbox
2. Archive
3. Delete
4. Create TickTick task + archive
5. Discuss more

## Step 6 — Convert ACTIONABLE items to TickTick tasks

Unless `--no-tasks` flag is set:

For each actionable item, ask the user which to convert to TickTick tasks.
Create tasks via `create_task` with:
- `title`: concise action ("Pay CPA invoice #16802 — $4,450")
- `content`: brief context (sender, amount, deadline, link if relevant)
- `priority`: 5 (high) for financial/expiring, 3 (medium) for replies, 1 (low) for low-urgency
- `dueDate`: set if there's a clear deadline (ISO 8601)
- `timeZone`: "America/Los_Angeles"

After tasks are created, archive the source emails.

## Step 7 — Report

```
─────────────────────────────────────────
Inbox Triage Complete — Page N

  Trashed:   {n} threads
  Archived:  {n} threads
  Tasks:     {n} created in TickTick
  Kept:      {n} threads still in inbox

Next: run again for next page, or inbox zero achieved.
─────────────────────────────────────────
```

Offer to continue to next page if `nextPageToken` exists.

## Notes

- Always flag starred items as ACTIONABLE regardless of content.
- For recruiter / job outreach: present in AMBIGUOUS, don't auto-delete.
- Financial records (receipts, statements): default to ARCHIVE not NOISE.
- Security alerts older than 30 days with no follow-up: NOISE.
- TickTick task titles must be concise — put detail in `content` field.
- Run label/unlabel calls in parallel batches of 10 for speed.
