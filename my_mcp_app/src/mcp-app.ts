import { App } from "@modelcontextprotocol/ext-apps";

interface Job {
  id: string;
  title: string;
  status: "needs_review" | "failed" | "approved" | "rejected";
  duration: string;
  error?: string;
  reason?: string;
}

const rowsEl = document.getElementById("rows")!;
const filterEl = document.getElementById("filter") as HTMLSelectElement;
const msgEl = document.getElementById("msg")!;
let jobs: Job[] = [];
// Row currently asking for a rejection reason. window.prompt() is blocked in sandboxed
// iframes (no allow-modals), so the reason is collected inline instead.
let rejectingId: string | null = null;

const app = new App({ name: "Render Job Board", version: "1.0.0" });

function textOf(result: { content?: Array<{ type: string; text?: string }> }): string {
  return result.content?.find((c) => c.type === "text")?.text ?? "";
}

function render() {
  const f = filterEl.value;
  rowsEl.replaceChildren();
  for (const job of jobs.filter((j) => f === "all" || j.status === f)) {
    const tr = document.createElement("tr");
    const cell = (text: string) => {
      const td = document.createElement("td");
      td.textContent = text;
      tr.appendChild(td);
      return td;
    };
    cell(job.id);
    cell(job.title);
    const badge = document.createElement("span");
    badge.className = `badge ${job.status}`;
    badge.textContent = job.status;
    cell("").appendChild(badge);
    cell(job.duration);
    cell(job.error ?? (job.reason ? `Rejected: ${job.reason}` : ""));
    const actions = cell("");
    if (job.status === "needs_review" && rejectingId === job.id) {
      const input = document.createElement("input");
      input.placeholder = "Reason";
      const confirm = document.createElement("button");
      confirm.textContent = "Confirm";
      confirm.onclick = () => {
        const reason = input.value.trim();
        if (!reason) {
          msgEl.textContent = "Enter a reason to reject.";
          return;
        }
        rejectingId = null;
        act("reject_job", { id: job.id, reason });
      };
      const cancel = document.createElement("button");
      cancel.textContent = "Cancel";
      cancel.onclick = () => {
        rejectingId = null;
        render();
      };
      actions.append(input, confirm, cancel);
    } else if (job.status === "needs_review") {
      const approve = document.createElement("button");
      approve.textContent = "Approve";
      approve.onclick = () => act("approve_job", { id: job.id });
      const reject = document.createElement("button");
      reject.textContent = "Reject";
      reject.onclick = () => {
        msgEl.textContent = "";
        rejectingId = job.id;
        render();
      };
      actions.append(approve, reject);
    }
    rowsEl.appendChild(tr);
  }
}

async function act(name: string, args: Record<string, unknown>) {
  msgEl.textContent = "";
  try {
    const result = await app.callServerTool({ name, arguments: args });
    const updated = JSON.parse(textOf(result)) as Job;
    jobs = jobs.map((j) => (j.id === updated.id ? updated : j));
    render();
  } catch (e) {
    msgEl.textContent = String(e);
  }
}

filterEl.addEventListener("change", render);

// Set before connect() so the initial tool result isn't missed.
app.ontoolresult = (result) => {
  try {
    const data = JSON.parse(textOf(result)) as { jobs: Job[]; filter?: string };
    jobs = data.jobs;
    if (data.filter) filterEl.value = data.filter;
    render();
  } catch {
    msgEl.textContent = "Could not parse tool result";
  }
};

app.connect();
