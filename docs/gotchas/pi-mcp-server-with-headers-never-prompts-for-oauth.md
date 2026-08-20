# An MCP server that needs OAuth just fails 401 in pi, with no authorization prompt

**pi-mcp-adapter disables OAuth for any MCP server that configures `headers`, so
a server whose endpoint wants OAuth stays permanently unauthorized — `/mcp` never
offers to authorize it, and every call fails with `invalid_token`.**

`supportsOAuth()` in `mcp-auth-flow.ts` returns `false` as soon as
`headers` is non-empty; configured headers are treated as the caller having
chosen its own auth. The server is still listed by `mcp({})` and still reports
"configured but not connected", which reads like a network or endpoint problem
rather than a deliberate auth decision.

Adding `auth: "oauth"` to the server entry re-enables the flow — that branch is
checked before the headers branch. Be aware the OAuth provider then sets its own
`Authorization` header, so an `Authorization` header in the config is the one
thing OAuth will fight over; a header under any other name coexists with it fine.

Wrong turns worth skipping: a 401 from such a server usually advises clearing the
client's stored tokens and reconnecting, which sends you looking for a stale
credential in the OS keyring. There is nothing to clear — no token was ever
requested. Removing the credential from `mcp.json` and expecting pi to fall back
to OAuth works, but only because it empties `headers`; that also throws away
header auth that may have been the working path.

**Confirmed:** 2026-08-20, against pi-mcp-adapter shipped with pi 0.84.2
(`mcp-auth-flow.ts:940`).
