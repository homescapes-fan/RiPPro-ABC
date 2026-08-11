""" Discord に投稿する。"""

import os
from pathlib import Path

import requests
from dotenv import load_dotenv

import json

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

API_BASE = "https://discord.com/api/v10"
USER_AGENT = "RiPPro-ABC-Bot (https://github.com/homescapes-fan/RiPPro-ABC, 0.1)"


def _headers():
    """Discord API に必要なヘッダを組み立てる。"""
    token = os.environ["DISCORD_BOT_TOKEN"]
    return {
        "Authorization": f"Bot {token}",
        "User-Agent": USER_AGENT,
    }


def create_thread(channel_id, name):
    """チャンネルに公開スレッドを作り、そのスレッドの ID を返す。"""
    payload = {
        "name": name,
        "type": 11,
        "auto_archive_duration": 10080,
    }
    response = requests.post(
        f"{API_BASE}/channels/{channel_id}/threads",
        headers=_headers(),
        json=payload,
        timeout=10,
    )

    if response.status_code >= 400:
        raise RuntimeError(f"Discord API エラー {response.status_code}: {response.text}")

    return response.json()["id"]


def post_message(channel_id, content, image_path=None, ping=False):
    """指定チャンネルに投稿する。image_path を渡すと画像を添付する。"""
    payload = {
        "content": content,
        "allowed_mentions": {"parse": ["users"]} if ping else {"parse":[]}
    }
    url = f"{API_BASE}/channels/{channel_id}/messages"

    if image_path is None:
        response = requests.post(url, headers=_headers(), json=payload, timeout=30)
    else:
        with open(image_path, "rb") as image:
            response = requests.post(
                url,
                headers=_headers(),
                data={"payload_json": json.dumps(payload)},
                files={"files[0]": (image_path.name, image, "image.png")},
                timeout=30,
            )

    if response.status_code >= 400:
        raise RuntimeError(f"Discord API エラー {response.status_code}: {response.text}")

    return response.json()


def main():
    channel_id = os.environ["DISCORD_CHANNEL_ID"]
    message = post_message(channel_id, "テスト投稿です")
    print("投稿しました。メッセージID:", message["id"])

if __name__ == "__main__":
    main()
