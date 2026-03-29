"""
discord_sandbox_client.py
Runs INSIDE the sandbox.
Calls Discord webhook directly using requests with SSL verification
disabled to handle the sandbox proxy's TLS interception.
"""

import os
import json
import requests
from dotenv import load_dotenv

load_dotenv('/sandbox/.env')

WEBHOOK_URL = os.getenv('DISCORD_WEBHOOK')

COLOR_SUCCESS = 5814783
COLOR_ERROR   = 16711680
COLOR_WARNING = 16776960
COLOR_INFO    = 8311585
COLOR_PENDING = 10197915
COLOR_PR      = 3447003

EMOJI_NUMBERS = ["1️⃣","2️⃣","3️⃣","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]


def _send(title, description, color=COLOR_SUCCESS):
    embed = {"title": title, "description": description, "color": color}
    resp = requests.post(WEBHOOK_URL, json={"embeds": [embed]}, verify=False, timeout=15)
    print("[Discord]", title, "→", resp.status_code)
    return resp.status_code


def send_github_alert(repo_name, repo_url, description=None, prefix_type=None):
    prefix_legend = {
        "()" : "🔄 Force-pushed to existing repo",
        "."  : "📄 Report + code + data",
        ";"  : "🖨️ Code with printed outputs",
        "`"  : "📑 Two PDFs + code + data",
    }
    push_type = prefix_legend.get(prefix_type or "", "🚀 New repo created")
    return _send(
        "✅ NemoClaw Project Pushed",
        "**" + repo_name + "**\n\n🔗 " + repo_url + "\n\n📝 " +
        (description or "No description") + "\n\n" + push_type
    )


def send_error_alert(error_msg):
    return _send("❌ Error", error_msg, COLOR_ERROR)


def send_pdf_audit_report(folder_results):
    low = [r for r in folder_results if r.get("confidence","").upper() == "LOW"]
    rows = ["`" + r["folder"] + "` → " + r["filename"] + " [" + r["classification"] + "]" +
            (" ⚠️" if r.get("confidence","").upper() == "LOW" else "")
            for r in folder_results]
    summary = ("\n\n**" + str(len(low)) + " flagged for review.**") if low else "\n\n✅ All high-confidence."
    return _send("📋 PDF Audit Report", "\n".join(rows) + summary,
                 COLOR_WARNING if low else COLOR_SUCCESS)


def send_discard_ready_notice(folders_with_discards):
    lines = []
    for item in folders_with_discards:
        lines.append("**" + item["folder"] + "**")
        for f in item.get("files", []):
            lines.append("  🗑️ `" + f + "`")
    body = "\n".join(lines) or "No DISCARD_ files found."
    return _send("🗑️ DISCARD Files Ready",
                 body + "\n\n`!confirm-delete` to delete  |  `!cancel-delete` to abort",
                 COLOR_WARNING)


def send_session_status(remaining_folders):
    lines = []
    for i, f in enumerate(remaining_folders[:10]):
        lines.append((EMOJI_NUMBERS[i] if i < len(EMOJI_NUMBERS) else str(i+1)+".") + " `" + f + "`")
    if len(remaining_folders) > 10:
        lines.append("\n_...and " + str(len(remaining_folders)-10) + " more._")
    return _send(
        "📂 Session Started — Remaining Folders",
        "\n".join(lines) + "\n\n• React with emoji or type `!process 1 3 5`\n• Or `!process all`",
        COLOR_INFO
    )


def send_folder_summary(folder_name, repo_name, renamed_files, metrics_source, warnings=None):
    renames = "\n".join(["  `" + o + "` → `" + n + "`" for o, n in renamed_files]) or "  No renames."
    warn_text = ("\n\n⚠️ **Review needed:**\n" + "\n".join("• " + w for w in warnings)) if warnings else ""
    return _send(
        "📦 Ready to Push: `" + repo_name + "`",
        "**Folder:** `" + folder_name + "`\n\n**Renames:**\n" + renames +
        "\n\n**Metrics:** " + metrics_source + warn_text +
        "\n\n`!proceed` to push  |  `!skip` to skip",
        COLOR_PENDING
    )


def send_session_complete(pushed, skipped, errors):
    return _send(
        "🏁 Session Complete",
        "**Pushed (" + str(len(pushed)) + "):**\n" +
        ("\n".join(["✅ [" + r + "](" + u + ")" for r, u in pushed]) or "None") +
        "\n\n**Skipped (" + str(len(skipped)) + "):**\n" +
        ("\n".join(["⏭️ " + r for r in skipped]) or "None") +
        "\n\n**Errors (" + str(len(errors)) + "):**\n" +
        ("\n".join(["❌ " + r + ": " + e for r, e in errors]) or "None"),
        COLOR_SUCCESS if not errors else COLOR_WARNING
    )


def send_old_repo_inference(repo_name, inferred_title, inferred_description, file_list):
    files = "\n".join(["  • `" + f + "`" for f in file_list]) or "  No files."
    return _send(
        "🔍 Inferred: `" + repo_name + "`",
        "**Title:** " + inferred_title + "\n\n**Description:** " + inferred_description +
        "\n\n**Files:**\n" + files +
        "\n\n`!approve " + repo_name + "` or `!skip " + repo_name + "`",
        COLOR_INFO
    )


def send_pr_ready(repo_name, new_repo_name, pr_url, branch="restructure", changes_summary=""):
    return _send(
        "🔀 PR Ready — `" + repo_name + "`",
        "**Branch:** `" + branch + "` -> `main`\n\n**PR:** " + pr_url +
        "\n\n**Changes:** " + (changes_summary or "File renames + README + requirements.txt + .gitignore") +
        "\n\n1. Review PR on GitHub\n2. Merge it\n3. Reply: `!rename-repo " + repo_name + " " + new_repo_name + "`",
        COLOR_PR
    )


def send_repo_renamed(old_name, new_name, new_url):
    return _send("✏️ Repo Renamed",
                 "`" + old_name + "` → **`" + new_name + "`**\n\n🔗 " + new_url)
