"""AtCoderから結果を取得"""

import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv
from perf import apply_cap, collect_aperfs, expected_rank, display_performanece, predict_performance, rated_ranks

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

    rated_rows = [row for row in standings["StandingsData"] if row["IsRated"]]
    rated_rows.sort(key=lambda row: row["Rank"])

    last_rank = rated_rows[-1]["Rank"]
    tail = [row for row in rated_rows if row["Rank"] == last_rank]
    # tail_perfs = sorted(
    #     {official[row["UserScreenName"]] for row in tail if row["UserScreenName"] in official}
    # )

    best = len(rated_rows) - len(tail) + 1
    worst = len(rated_rows)
    perf = official[tail[0]["UserScreenName"]]
    implied = expected_rank(perf, aperf_list) + 0.5
    submitted = sum(1 for row in tail if row["TotalResult"]["Count"] > 0)
    in_official = sum(1 for row in tail if row["UserScreenName"] in official)
    tail_name = tail[0]["UserScreenName"]
    raw = predict_performance(ranks[tail_name], aperf_list)

    print(contest_id)
    print(f"  rated 総数        : {worst}")
    print(f"  最下位グループ     : {best} ~ {worst} （{len(tail)}人）")
    print(f"  うち提出ありの人   : {submitted} 人")
    print(f"  公式perf          : {perf}")
    print(f"  逆算した順位       : {implied:.1f}")
    print(f"  best からの差      : {implied - best:.1f}")
    print(f"  グループ内の割合   : {(implied - best) / (worst - best):.3f}")
    print(f"  best + 提出ありの人: {best + submitted}")
    print(f"  result/json にいる人: {in_official} 人")
    print(f"最下位グループ 生の値={raw} 表示={display_performanece(apply_cap(raw, contest_id))}")

    # print(f"rated 参加者 {len(rated_rows)} 人")
    # print(f"最下位グループ Rank={last_rank} 人数={len(tail)}")
    # print(f"そのグループの公式perf: {tail_perfs[:5]} （全 {len(tail_perfs)} 種類）")
    # print()

    # step =  max(1, len(rated_rows) // 20)
    # print("こちらの順位    公式perf    逆算した順位")
    # for row in rated_rows[::step]:
    #     name = row["UserScreenName"]
    #     actual = official.get(name)
    #     if actual is None:
    #         continue
    #     implied = expected_rank(actual, aperf_list) + 0.5
    #     print(f"{ranks[name]:>12}  {actual:>8}  {implied:>13.1f}")


if __name__ == "__main__":
    main()