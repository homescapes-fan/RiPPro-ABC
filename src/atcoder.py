"""AtCoderから結果を取得"""

import os
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv, set_key
from perf import (
    apply_cap,
    collect_aperfs,
    display_performanece,
    predict_performance,
    rated_rank_resolver,
)
from rating import predict_new_rating

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

USER_AGENT = "RiPPro-ABC-Bot(https://github.com/homescapes-fan/RiPPro-ABC)"

# コンテストが実際に行われたと判断する提出数のしきい値
# Tester や解説放送の担当者が開始前に提出することがあるため敢えてこの値にしている。
MIN_SUBMISSIONS = 1000

# 429（レート制限）を返されたときに待つ秒数。
RETRY_WAIT = 10.2


def _get(url, **kwargs):
    """GET する。429 が返ったら少し待って1回だけやり直す。"""
    response = requests.get(url, **kwargs)

    if response.status_code == 429:
        time.sleep(RETRY_WAIT)
        response = requests.get(url, **kwargs)

    return response


def fetch_results(contest_id):
    """指定したコンテストの全参加者の結果を取得し、リストで返す"""
    url = f"https://atcoder.jp/contests/{contest_id}/results/json"
    response = _get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
    response.raise_for_status()
    return response.json()


def fetch_standings(contest_id):
    """順位表の取得（AtCoderのログインセッションが必要）"""
    session = os.environ.get("ATCODER_SESSION", "")
    if not session:
        raise RuntimeError(".env の ATCODER_SESSION が読み込めていません。")
    
    url = f"https://atcoder.jp/contests/{contest_id}/standings/json"
    response = _get(
        url,
        headers={"User-Agent": USER_AGENT},
        cookies={"REVEL_SESSION": session},
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

    new_session = response.cookies.get("REVEL_SESSION")
    if new_session and new_session != session:
        set_key(str(ENV_PATH), "ATCODER_SESSION", new_session)

    return response.json()


def fetch_aperfs(contest_id):
    """ac-predictorが配信している aperf（過去成績の重み付き平均）を取得。無ければ None"""
    url = f"https://data.ac-predictor.com/aperfs/{contest_id}.json"
    response = _get(url, headers={"User-Agent": USER_AGENT}, timeout=30)

    if response.status_code == 404:
        return None

    response.raise_for_status()
    return response.json()


def fetch_history(user):
    """ユーザーのコンテスト履歴を取得"""
    url = f"https://atcoder.jp/users/{user}/history/json"
    response = _get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
    response.raise_for_status()
    return response.json()


def history_before(history, contest_id):
    """指定コンテント以降のリ履歴を取り除く"""
    screen_name = f"{contest_id}.contest.atcoder.jp"
    for index, entry in enumerate(history):
        if entry["ContestScreenName"] == screen_name:
            return history[:index]
    return history


def total_submissions(standings):
    """全参加者の提出回数の合計を返す。"""
    return sum(row["TotalResult"]["Count"] for row in standings["StandingsData"])


def main():
    contest_id = sys.argv[1] if len(sys.argv) > 1 else "abc470"
    names = sys.argv[2:] or ["riru06", "homescapes_fan", "Show_541", "Silver2300", "zabesu210", "takuan1", "sho0u"]

    standings = fetch_standings(contest_id)
    aperfs = fetch_aperfs(contest_id)
    aperf_list = collect_aperfs(standings, aperfs, contest_id)
    resolve = rated_rank_resolver(standings)
    row_of = {row["UserScreenName"]: row for row in standings["StandingsData"]}

    screen_name = f"{contest_id}.contest.atcoder.jp"

    for user in names:
        row = row_of.get(user)
        if row is None:
            print(f"{user}: 不参加")
            continue

        raw = apply_cap(predict_performance(resolve(row["Rank"]), aperf_list), contest_id)

        history = fetch_history(user)
        index = next(
            i for i, e in enumerate(history) if e["ContestScreenName"] == screen_name
        )
        actual = history[index]
        before = history[:index]

        old, new = predict_new_rating(before, raw)
        print(
            f"{user}: perf={raw} 予測 {old} -> {new} / 実際 "
            f"{actual['OldRating']} -> {actual['NewRating']}"
        )


if __name__ == "__main__":
    main()