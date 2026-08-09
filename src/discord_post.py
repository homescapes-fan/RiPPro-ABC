""" Discord に投稿する。"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

API_BASE = "https://discord.com/api/v10"
USER_AGENT = "RiPPro-ABC-Bot (https://github.com/homescapes-fan/RiPPro-ABC, 0.1)"


def _headers():
    """Discord API に必要なヘッダを組み立てる"""
    token = os.environ["DISCORD_BOT_TOKEN"]
    return {
        "Authorization": f"Bot {token}",
        "User-Agent": USER_AGENT,
    }

def post_message(channel_id, content, ping=False):
    """指定のチャンネルにテキストを投稿"""
    payload = {
        "content": content,
        "allowed_mentions": {"parse": ["users"]} if ping else {"parse":[]}
    }

    response = requests.post(
        f"{API_BASE}/channels/{channel_id}/messages",
        headers=_headers(),
        json=payload,
        timeout=10,
    )

    if response.status_code >= 400:
        raise RuntimeError(
            f"Discord API エラー {response.status_code}: {response.text}"
        )

    return response.json()

def main():
    channel_id = os.environ["DISCORD_CHANNEL_ID"]
    message = post_message(channel_id, "テスト投稿です")
    print("投稿しました。メッセージID:", message["id"])

if __name__ == "__main__":
    main()
