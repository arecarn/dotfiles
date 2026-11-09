---
description: Walk through a list of items one at a time, presenting each with enough context to decide and acting on the user's choice. Use when the user says "walk me through these", "/walkthrough", "one by one", "go through these individually", "let's take these one at a time", or when a response contains a list the user wants to address item-by-item.
argument-hint: "[list source or topic]"
model: haiku
---

# Walkthrough

Go through a list one item at a time.

1. **List.** Take the items from the conversation or `$ARGUMENTS`. Ask only if
   the scope is unclear. State the total.
2. **Each item.** Show `Item N of M: <title>`, just enough context to decide,
   and up to three options. Prefer `AskUserQuestion` when available (its
   built-in "Other" covers a custom answer; include a **Discuss** option);
   otherwise use a numbered list that also allows a custom answer and
   **discuss**. On discuss, stay on the item until they decide. Show one item
   at a time.
3. **Act.** Apply each decision right away. If it writes prose to an external
   system, show the exact text and get a yes first, per the global review rule.
4. **Finish.** Give a short list of what was decided for each item and what was
   skipped.

If the user says **stop** or **just do them all**, do that and summarize what
remains.
