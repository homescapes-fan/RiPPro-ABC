"""AtCoderから結果を取得"""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

USER_AGENT = "RiPPro-ABC-Bot(https://github.com/homescapes-fan/RiPPro-ABC)"

def fetch_results(contest_id):
    """指定したコンテストの全参加者の結果を取得し、リストで返す"""
    url = f"https://atcoder.jp/contests/{contest_id}/results/json"
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_standings(contest_id):
    """順位表の取得（AtCoderのログインセッションが必要）"""
    session = os.environ.get("ATCODER_SESSION", "")
    if not session:
        raise RuntimeError(".env の ATCODER_SESSION が読み込めていません。")
    
    url = f"https://atcoder.jp/contests/{contest_id}/standings/json"
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        cookies={"REVEL_SESSION": os.environ["ATCODER_SESSION"]},
        timeout=30,
    )
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "")
    if "json" not in content_type:
        raise RuntimeError(
            "JSON が返りませんでした。 \n"
            f"  status       = {response.status_code}\n"
            f"  Content-Type = {content_type}\n"
            f"  最終URL      = {response.url}\n"
            f"  本文の先頭    = {response.text[:200]!r}"
        )

    return response.json()


def main():
    contest_id = sys.argv[1] if len(sys.argv) > 1 else "abc470"

    standings = fetch_standings(contest_id)

    print("トップレベルのキー", list(standings.keys()))
    print("問題", [t["Assignment"] for t in standings["TaskInfo"]])
    print("行数", len(standings["StandingsData"]))

    first = standings["StandingsData"][0]
    print()
    print("1行目のキー:", list(first.keys()))
    print("Rank", first["Rank"], "/ User:", first["UserScreenName"])
    print("TotalResult:", first["TotalResult"])

    print()
    print("TaskInfo の1件:", standings["TaskInfo"][0])

    target = "homescapes_fan"
    member_row = next(
        (r for r in standings["StandingsData"] if r["UserScreenName"] == target),
        None,
    )
    if member_row is None:
        print(f"{target} は参加していません")
    else:
        print(f"{target} の TaskResults")
        for task_key, result in member_row["TaskResults"].items():
            print(" ", task_key, result)

if __name__ == "__main__":
    main()