import json
import os
from pathlib import Path

from mcp.server.apps import Apps
from mcp.server.mcpserver import MCPServer
from mcp.server.transport_security import TransportSecuritySettings
from starlette.middleware.cors import CORSMiddleware

# Bump the version suffix whenever the view changes: hosts like Claude cache the view by URI.
UI_URI = "ui://render-jobs/board-v2.html"
HTML = (Path(__file__).parent / "dist" / "mcp-app.html").read_text()

# In-memory state; resets on restart.
JOBS: dict[str, dict] = {
    j["id"]: j
    for j in [
        {"id": "job-001", "title": "Product Launch Teaser", "status": "needs_review", "duration": "0:45"},
        {"id": "job-002", "title": "Weekly Recap Episode 12", "status": "needs_review", "duration": "3:12"},
        {"id": "job-003", "title": "Customer Story: Acme", "status": "failed", "duration": "2:30",
         "error": "FFmpeg exited 1: missing audio stream in asset narration.wav"},
        {"id": "job-004", "title": "Tutorial: Getting Started", "status": "approved", "duration": "5:08"},
        {"id": "job-005", "title": "Holiday Promo", "status": "failed", "duration": "1:00",
         "error": "S3 AccessDenied fetching s3://assets/holiday/bg.mp4"},
        {"id": "job-006", "title": "Feature Update Reel", "status": "needs_review", "duration": "0:58"},
        {"id": "job-007", "title": "Intro Bumper v2", "status": "rejected", "duration": "0:10",
         "reason": "Logo is off-center"},
        {"id": "job-008", "title": "Q4 Investor Update", "status": "failed", "duration": "8:41",
         "error": "Render timed out after 900s on GPU worker g5.xlarge"},
    ]
}

apps = Apps()


@apps.tool(resource_uri=UI_URI, name="show_jobs", title="Show Render Jobs",
           description="Open the render job approval board, optionally pre-filtered by status "
                       "(needs_review, failed, approved, rejected).")
def show_jobs(status: str | None = None) -> str:
    return json.dumps({"jobs": list(JOBS.values()), "filter": status or "all"})


@apps.tool(resource_uri=UI_URI, visibility=["app"], name="approve_job",
           description="Approve a job awaiting review. Called by the UI only.")
def approve_job(id: str) -> str:
    job = _reviewable(id)
    job["status"] = "approved"
    return json.dumps(job)


@apps.tool(resource_uri=UI_URI, visibility=["app"], name="reject_job",
           description="Reject a job awaiting review with a reason. Called by the UI only.")
def reject_job(id: str, reason: str) -> str:
    job = _reviewable(id)
    job["status"] = "rejected"
    job["reason"] = reason
    return json.dumps(job)


# MCPServer snapshots extension tools/resources at construction, so build it after
# every apps.tool / add_html_resource call.
apps.add_html_resource(UI_URI, HTML, title="Render Job Board")
mcp = MCPServer("render-job-board", extensions=[apps])


@mcp.tool(description="Summarize all failed render jobs and their error messages.")
def summarize_failures() -> str:
    failed = [j for j in JOBS.values() if j["status"] == "failed"]
    if not failed:
        return "No failed jobs."
    return f"{len(failed)} failed job(s):\n" + "\n".join(
        f"- {j['id']} ({j['title']}): {j['error']}" for j in failed
    )


def _reviewable(job_id: str) -> dict:
    job = JOBS.get(job_id)
    if job is None:
        raise ValueError(f"Unknown job {job_id}")
    if job["status"] != "needs_review":
        raise ValueError(f"Job {job_id} is {job['status']}, not needs_review")
    return job


# DNS-rebinding protection stays on. The SDK only allows localhost by default, so a tunnel's
# hostname gets a 421. Add it via TUNNEL_HOST=<name>.ngrok-free.dev (no scheme, no path).
_tunnel = [h for h in os.environ.get("TUNNEL_HOST", "").split(",") if h]
app = mcp.streamable_http_app(
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=["127.0.0.1:*", "localhost:*", "[::1]:*", *_tunnel],
        allowed_origins=[
            "http://127.0.0.1:*", "http://localhost:*", "http://[::1]:*",
            *[f"https://{h}" for h in _tunnel],
        ],
    )
)
# Only the ext-apps basic host may call this server from a browser. Claude's connector
# talks to the server from its backend, so it doesn't need CORS. Override with
# ALLOWED_ORIGINS="https://a.example,https://b.example" if you use another host.
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080"
).split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["content-type", "mcp-session-id", "mcp-protocol-version", "authorization"],
    expose_headers=["mcp-session-id"],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=3001)
