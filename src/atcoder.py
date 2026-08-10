"""AtCoderから結果を取得"""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from perf import apply_cap, collect_aperfs, predict_performance, rated_ranks

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


def fetch_aperfs(contest_id):
    """ac-predictorが配信している aperf（過去成績の重み付き平均）を取得"""
    url = f"https://data.ac-predictor.com/aperfs/{contest_id}.json"
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    response.raise_for_status()
    return response.json()


def main():
    contest_id = sys.argv[1] if len(sys.argv) > 1 else "abc470"

    standings = fetch_standings(contest_id)
    aperfs = fetch_aperfs(contest_id)
    results = fetch_results(contest_id)

    aperf_list = collect_aperfs(standings, aperfs, contest_id)
    ranks = rated_ranks(standings)
    official = {row["UserScreenName"]: row["Performance"] for row in results}

    # print(f"rated 参加者: {len(aperf_list)} 人")
    # print()

    # for name in ["homescapes_fan", "Show_541", "Silver2300", "zabesu210"]:
    #     rated_rank = ranks.get(name)
    #     if rated_rank is None:
    #         print(f"{name}: rated 参加していません")
    #         continue

    #     predicted = predict_performance(rated_rank, aperf_list)
    #     print(f"{name}: rated順位={rated_rank} 予測={predicted} 公式={official.get(name)}")

    rated_rows = [row for row in standings["StandingsData"] if row["IsRated"]]
    rated_rows.sort(key=lambda row: row["Rank"])
    step =  max(1, len(rated_rows) // 20)

    print("rated順位    予測    公式     差")
    for row in rated_rows[::step]:
        name = row["UserScreenName"]
        actual = official.get(name)
        if actual is None:
            continue
        predicted = apply_cap(predict_performance(ranks[name], aperf_list), contest_id)
        print(f"{ranks[name]:>8}  {predicted:>6}  {actual:>6}  {actual - predicted:>+6}")


if __name__ == "__main__":
    main()