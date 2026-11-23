# Render Job Approval Board (MCP App)

Python MCP server (in-memory jobs) + single-file Vite view.

```bash
npm install && npm run build          # builds dist/mcp-app.html
source ../.venv/bin/activate
python server.py                      # http://127.0.0.1:3001/mcp
```

Tools: `show_jobs(status?)` (opens UI), `summarize_failures()` (model-facing),
`approve_job(id)` / `reject_job(id, reason)` (`visibility=["app"]`, called by buttons).

Test in the ext-apps basic host (`examples/basic-host`, `npm start`, http://localhost:8080),
or in Claude via `npx cloudflared tunnel --url http://localhost:3001` and add `<url>/mcp` as a connector.
Jobs reset when the server restarts.
