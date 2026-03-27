import requests
import os
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")

def send_alert(title, description, color=5814783):
    data = {
        "embeds": [
            {
                "title": title,
                "description": description,
                "color": color
            }
        ]
    }

    requests.post(WEBHOOK_URL, json=data)

def send_github_alert(repo_name, repo_url, description=None):
    send_alert(
        "🚀 NemoClaw Project Pushed",
        f"**{repo_name}**\n\n🔗 {repo_url}\n\n📝 {description or 'No description'}"
    )

def send_error_alert(error_msg):
    send_alert(
        "❌ Error",
        error_msg,
        color=16711680
    )