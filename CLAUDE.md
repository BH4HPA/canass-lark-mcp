# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a configuration repository (no build/test/lint) that sets up Lark (Feishu) integration for Claude Code. Uses a hybrid approach:
- **MCP server** (read-only, 7 tools, ~10K schema) for reading docs, comments, and permissions
- **`lark_api.py`** (direct API calls, zero context cost) for all write operations

All API calls use `tenant_access_token` (app identity, not user identity).

## Commands

```bash
bash start.sh                                           # Start MCP server (read-only tools)
python3 lark_api.py <METHOD> '<API_PATH>' ['<JSON>']    # Direct API call (write operations)
```

Requires `LARK_APP_ID` and `LARK_APP_SECRET` in `.env` (see `.env.example`).

## Architecture

- `start.sh` — MCP server entry point; loads `.env`, runs `npx @larksuiteoapi/lark-mcp` with read-only tool whitelist
- `lark_api.py` — Lightweight script for direct Lark Open API calls; handles auth automatically, zero context overhead
- `mcp-config.json` — Template `.mcp.json` for other repos
- `AGENTS.md` — **The most important file**: team member open_ids, MCP tool reference, API endpoint reference, wiki token resolution workflow, document creation/editing patterns, and block type codes
- `permissions.json` — Records which Lark scopes the app has been granted (reference only)

## Key Concepts

- **Wiki token vs obj_token**: Wiki documents require a `wiki_v2_space_getNode` call to convert the wiki token to a docx `obj_token` before editing. Reading can use the wiki token directly; editing requires the obj_token.
- **App-created vs user-owned docs**: The app has full control over docs it creates. For user-owned docs, the user must grant the app edit/manage permissions explicitly.
- **Never set `useUAT: true`** in MCP tool calls — always use the default app identity.
- **Testing**: When testing API calls (sending messages, transferring docs), use Ray's open_id, not Canass's, to avoid disturbing the end user.

## Integration Pattern

Other repos integrate by:
1. Pointing their `.mcp.json` at `start.sh` (see `mcp-config.json`)
2. Copying/referencing `AGENTS.md` for agent instructions
3. Ensuring `lark_api.py` is accessible by absolute path for write operations
