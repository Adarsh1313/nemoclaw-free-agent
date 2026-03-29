"""
discord_sandbox_client.py
Runs INSIDE the sandbox.
Instead of calling Discord directly (blocked by sandbox proxy),
it calls the discord_relay.py server running on the Codespace host
via http://10.200.0.1:9876/

NemoClaw uses this file inside the sandbox for all Discord notifications.
The relay server on the host forwards everything to Discord.

Usage (inside sandbox):
    import sys
    sys.path.insert(0, '/sandbox')
    from discord_sandbox_client import *
"""

import json
import urllib.request
import urllib.error

RELAY_URL = "http://10.200.0.1:9876"


def _call_relay(action: str, payload: dict):
    """Send a JSON POST to the relay server on the host."""
    url  = RELAY_URL + "/" + action
    data = json.dumps(payload).encode()
    req  = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            print("[Discord] " + action + " → " + str(result))
            return result
    except urllib.error.URLError as e:
        print("[Discord] Relay unreachable: " + str(e))
        print("[Discord] Is discord_relay.py running on the host?")
        return {"error": str(e)}


# ── Public functions (same interface as discord_alerts.py) ────────────────────

def send_github_alert(repo_name, repo_url, description=None, prefix_type=None):
    return _call_relay("send_github_alert", {
        "repo_name": repo_name,
        "repo_url": repo_url,
        "description": description or "",
        "prefix_type": prefix_type or ""
    })


def send_error_alert(error_msg):
    return _call_relay("send_error_alert", {"error_msg": error_msg})


def send_pdf_audit_report(folder_results):
    return _call_relay("send_pdf_audit_report", {"folder_results": folder_results})


def send_discard_ready_notice(folders_with_discards):
    return _call_relay("send_discard_ready_notice", {"folders_with_discards": folders_with_discards})


def send_session_status(remaining_folders):
    return _call_relay("send_session_status", {"remaining_folders": remaining_folders})


def send_folder_summary(folder_name, repo_name, renamed_files, metrics_source, warnings=None):
    return _call_relay("send_folder_summary", {
        "folder_name": folder_name,
        "repo_name": repo_name,
        "renamed_files": renamed_files,
        "metrics_source": metrics_source,
        "warnings": warnings or []
    })


def send_session_complete(pushed, skipped, errors):
    return _call_relay("send_session_complete", {
        "pushed": pushed,
        "skipped": skipped,
        "errors": errors
    })


def send_old_repo_inference(repo_name, inferred_title, inferred_description, file_list):
    return _call_relay("send_old_repo_inference", {
        "repo_name": repo_name,
        "inferred_title": inferred_title,
        "inferred_description": inferred_description,
        "file_list": file_list
    })


def send_pr_ready(repo_name, new_repo_name, pr_url, branch="restructure", changes_summary=""):
    return _call_relay("send_pr_ready", {
        "repo_name": repo_name,
        "new_repo_name": new_repo_name,
        "pr_url": pr_url,
        "branch": branch,
        "changes_summary": changes_summary
    })


def send_repo_renamed(old_name, new_name, new_url):
    return _call_relay("send_repo_renamed", {
        "old_name": old_name,
        "new_name": new_name,
        "new_url": new_url
    })
