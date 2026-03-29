"""
discord_relay.py
Runs on the Codespace HOST (outside sandbox).
Receives HTTP calls from inside the sandbox via localhost:9876
and forwards them to Discord webhook + bot.

Start this alongside discord_bot_runner.py via startup.sh.
The sandbox calls http://10.200.0.1:9876/ (the host IP visible from sandbox).
"""

import os
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv
import requests

load_dotenv()

WEBHOOK_URL  = os.getenv("DISCORD_WEBHOOK")
RELAY_PORT   = 9876
HOST_IP      = "0.0.0.0"  # listen on all interfaces so sandbox can reach it

# ── Colors ────────────────────────────────────────────────────────────────────
COLOR_SUCCESS = 5814783
COLOR_ERROR   = 16711680
COLOR_WARNING = 16776960
COLOR_INFO    = 8311585
COLOR_PENDING = 10197915
COLOR_PR      = 3447003


def _send_webhook(title: str, description: str, color: int = COLOR_SUCCESS):
    embed = {"title": title, "description": description, "color": color}
    resp = requests.post(WEBHOOK_URL, json={"embeds": [embed]}, timeout=10)
    resp.raise_for_status()
    return {"ok": True}


# ── Request handler ───────────────────────────────────────────────────────────

class RelayHandler(BaseHTTPRequestHandler):

    def log_message(self, format, *args):
        print(f"[Relay] {args[0]} {args[1]}")

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body   = self.rfile.read(length)

        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            self._respond(400, {"error": "invalid JSON"})
            return

        action = self.path.lstrip("/")
        result = self._dispatch(action, payload)
        self._respond(200, result)

    def _respond(self, status: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def _dispatch(self, action: str, p: dict):
        try:
            if action == "send_github_alert":
                prefix_legend = {
                    "()" : "🔄 Force-pushed to existing repo",
                    "."  : "📄 Report + code + data",
                    ";"  : "🖨️ Code with printed outputs",
                    "`"  : "📑 Two PDFs + code + data",
                }
                push_type = prefix_legend.get(p.get("prefix_type", ""), "🚀 New repo created")
                return _send_webhook(
                    "✅ NemoClaw Project Pushed",
                    "**" + p.get("repo_name","") + "**\n\n"
                    "🔗 " + p.get("repo_url","") + "\n\n"
                    "📝 " + p.get("description", "No description") + "\n\n"
                    + push_type,
                    COLOR_SUCCESS
                )

            elif action == "send_error_alert":
                return _send_webhook("❌ Error", p.get("error_msg",""), COLOR_ERROR)

            elif action == "send_pdf_audit_report":
                results = p.get("folder_results", [])
                low = [r for r in results if r.get("confidence","").upper() == "LOW"]
                rows = []
                for r in results:
                    flag = " ⚠️" if r.get("confidence","").upper() == "LOW" else ""
                    rows.append("`" + r["folder"] + "`  →  " + r["filename"] + "  [" + r["classification"] + "]" + flag)
                description = "\n".join(rows) or "No PDFs found."
                summary = ("\n\n**" + str(len(low)) + " item(s) flagged for manual review.**") if low else "\n\n✅ All high-confidence."
                return _send_webhook("📋 PDF Audit Report — Phase 0", description + summary,
                                     COLOR_WARNING if low else COLOR_SUCCESS)

            elif action == "send_discard_ready_notice":
                items = p.get("folders_with_discards", [])
                lines = []
                for item in items:
                    lines.append("**" + item["folder"] + "**")
                    for f in item.get("files", []):
                        lines.append("  🗑️ `" + f + "`")
                description = "\n".join(lines) or "No DISCARD_ files found."
                return _send_webhook(
                    "🗑️ DISCARD Files Ready for Deletion",
                    description + "\n\n**Reply:**\n`!confirm-delete` — delete all\n`!cancel-delete` — abort",
                    COLOR_WARNING
                )

            elif action == "send_session_status":
                folders = p.get("remaining_folders", [])
                emoji   = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]
                lines   = []
                for i, f in enumerate(folders[:10]):
                    lines.append((emoji[i] if i < len(emoji) else str(i+1)+".") + " `" + f + "`")
                if len(folders) > 10:
                    lines.append("\n_...and " + str(len(folders)-10) + " more. Type `!process 11 12` for those._")
                return _send_webhook(
                    "📂 NemoClaw Session Started — Remaining Folders",
                    "\n".join(lines) + "\n\n"
                    "**Select folders:**\n"
                    "• React with emoji numbers\n"
                    "• Or type: `!process 1 3 5`\n"
                    "• Or type: `!process all`",
                    COLOR_INFO
                )

            elif action == "send_folder_summary":
                renames   = p.get("renamed_files", [])
                warnings  = p.get("warnings", [])
                rename_text = "\n".join(["  `" + o + "` → `" + n + "`" for o,n in renames]) or "  No renames."
                warn_text   = ("\n\n⚠️ **Needs review:**\n" + "\n".join("• "+w for w in warnings)) if warnings else ""
                return _send_webhook(
                    "📦 Ready to Push: `" + p.get("repo_name","") + "`",
                    "**Source folder:** `" + p.get("folder_name","") + "`\n\n"
                    "**File renames:**\n" + rename_text + "\n\n"
                    "**Metrics found in:** " + p.get("metrics_source","unknown")
                    + warn_text + "\n\n"
                    "**Reply:** `!proceed` to push  |  `!skip` to skip",
                    COLOR_PENDING
                )

            elif action == "send_session_complete":
                pushed  = p.get("pushed", [])
                skipped = p.get("skipped", [])
                errors  = p.get("errors", [])
                pushed_text  = "\n".join(["✅ [" + r + "](" + u + ")" for r,u in pushed]) or "None"
                skipped_text = "\n".join(["⏭️ " + r for r in skipped]) or "None"
                error_text   = "\n".join(["❌ " + r + ": " + e for r,e in errors]) or "None"
                return _send_webhook(
                    "🏁 Session Complete",
                    "**Pushed (" + str(len(pushed)) + "):**\n" + pushed_text + "\n\n"
                    "**Skipped (" + str(len(skipped)) + "):**\n" + skipped_text + "\n\n"
                    "**Errors (" + str(len(errors)) + "):**\n" + error_text,
                    COLOR_SUCCESS if not errors else COLOR_WARNING
                )

            elif action == "send_old_repo_inference":
                files = "\n".join(["  • `" + f + "`" for f in p.get("file_list", [])]) or "  No files."
                return _send_webhook(
                    "🔍 Inferred: `" + p.get("repo_name","") + "`",
                    "**Inferred title:** " + p.get("inferred_title","") + "\n\n"
                    "**Description:** " + p.get("inferred_description","") + "\n\n"
                    "**Files:**\n" + files + "\n\n"
                    "**Reply:**\n"
                    "`!approve " + p.get("repo_name","") + "` — create branch + PR\n"
                    "`!skip " + p.get("repo_name","") + "` — skip",
                    COLOR_INFO
                )

            elif action == "send_pr_ready":
                return _send_webhook(
                    "🔀 PR Ready — `" + p.get("repo_name","") + "`",
                    "**Branch:** `" + p.get("branch","restructure") + "` -> `main`\n\n"
                    "**Pull Request:** " + p.get("pr_url","") + "\n\n"
                    "**Changes:** " + p.get("changes_summary","File renames + README + requirements.txt + .gitignore") + "\n\n"
                    "**Steps:**\n"
                    "1. Review the PR on GitHub\n"
                    "2. Merge it yourself\n"
                    "3. Then reply: `!rename-repo " + p.get("repo_name","") + " " + p.get("new_repo_name","") + "`",
                    COLOR_PR
                )

            elif action == "send_repo_renamed":
                return _send_webhook(
                    "✏️ Repo Renamed",
                    "`" + p.get("old_name","") + "` → **`" + p.get("new_name","") + "`**\n\n"
                    "🔗 " + p.get("new_url",""),
                    COLOR_SUCCESS
                )

            else:
                return {"error": "unknown action: " + action}

        except Exception as e:
            print(f"[Relay] Error in {action}: {e}")
            return {"error": str(e)}


# ── Start server ──────────────────────────────────────────────────────────────

def start_relay(port: int = RELAY_PORT):
    server = HTTPServer((HOST_IP, port), RelayHandler)
    print(f"[Relay] Listening on {HOST_IP}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    start_relay()
