"""RiPPro-ABC Bot の入口"""

import json
import sys
import os
import traceback
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from atcoder import (
    MIN_SUBMISSIONS,
    fetch_aperfs,
    fetch_history,
    fetch_standings,
    history_before,
    total_submissions,
    )
from perf import (
    apply_cap,
    collect_aperfs,
    display_performanece,
    predict_performance,
    rated_rank_resolver,
)
from table import build_rows, build_summary
from rating import predict_new_rating
from render import render
from discord_post import create_thread, post_message, notify_owner

MEMBERS_PATH = Path(__file__).resolve().parent.parent / "members.json"
STATE_PATH = Path(__file__).resolve().parent.parent / "state.json"

# AtCoder への連続アクセスを避けるための待ち時間（秒）。
# 参加者の人数だけ history/json を叩くため、間隔を空けないと 429 を返される。
REQUEST_INTERVAL = 0.5


def load_members():
    """ members.json を読み込みリストで返す"""
    with MEMBERS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def load_state():
    """前回までの状態を読み込む"""
    if not STATE_PATH.exists():
        raise RuntimeError(
            f"{STATE_PATH} がありません。"
            '{"last_contest": "abc470"} のような内容で作ってください。'
        )
    with STATE_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def save_state(state):
    """状態を書き出す"""
    with STATE_PATH.open("w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def next_contest_id(state):
    """次に扱うコンテスト ID を返す"""
    number = int(state["last_contest"].removeprefix("abc")) + 1
    return f"abc{number}"


def attach_rating(rows, contest_id, with_perf):
    """各行にレート情報を追加する。

    with_perf が偽のときは、履歴から取れる old_rating と rated_count だけを入れる。
    """
    for index, row in enumerate(rows):
        if index > 0:
            time.sleep(REQUEST_INTERVAL)

        history = history_before(fetch_history(row["user"]), contest_id)
        rated = [entry for entry in history if entry["IsRated"]]

        row["rated_count"] = len(rated)
        row["old_rating"] = rated[-1]["NewRating"] if rated else 0

        if with_perf:
            _, new = predict_new_rating(history, row["raw_perf"])
            row["new_rating"] = new if row["is_rated"] else None
        else:
            row["new_rating"] = None


def attach_performance(rows, standings, aperfs, contest_id):
    """各行に表示用の perf を追加"""
    aperf_list = collect_aperfs(standings, aperfs, contest_id)
    resolve = rated_rank_resolver(standings)

    for row in rows:
        rated_rank = resolve(row["rank"])
        raw = apply_cap(predict_performance(rated_rank, aperf_list), contest_id)
        row["raw_perf"] = raw
        row["perf"] = display_performanece(raw)


def build_mentions(rows):
    """参加者へのメンション文字列を作る。"""
    names = []
    for row in rows:
        discord_id = row["member"].get("discord_id")
        names.append(f"<@{discord_id}>" if discord_id else row["user"])
    return " ".join(names)


def main():
    args = [value for value in sys.argv[1:] if not value.startswith("--")]
    should_post = "--post" in sys.argv

    state = load_state()
    if args:
        contest_id = args[0]
        auto = False
    else:
        contest_id = next_contest_id(state)
        auto = True

    print("対象:", contest_id)

    standings = fetch_standings(contest_id)
    submissions = total_submissions(standings)
    print("提出合計:", submissions)

    if submissions < MIN_SUBMISSIONS:
        print(f"{contest_id} はまだ開催されていません")
        if auto and should_post:
            notify_owner(f"今週は ABC が開催されませんでした（{contest_id.upper()} は未開催）")
        return

    members = load_members()
    aperfs = fetch_aperfs(contest_id)
    with_rating = aperfs is not None
    if not with_rating:
        print("aperf が配信されていないため、perf とレート変化は表示しません")

    tasks, rows = build_rows(standings, members)
    if with_rating:
        attach_performance(rows, standings, aperfs, contest_id)
    attach_rating(rows, contest_id, with_rating)
    summary = build_summary(tasks, rows)

    headers = ["順位", "ユーザ", "得点"] + tasks
    if with_rating:
        headers += ["perf", "レート変化"]

    print(f"{contest_id}: 登録 {len(members)} 人中 {len(rows)} 人が参加")
    print(" | ".join(headers))

    for index, row in enumerate(rows, start=1):
        cell_texts = [
            f"{c['score']}{c['penalty']} {c['time']}".strip() for c in row["cells"]
        ]
        parts = [
            f"{index}({row['rank']})",
            row["user"],
            f"{row['total']['score']}{row['total']['penalty']}" or "-",
        ] + cell_texts

        if with_rating:
            if row["new_rating"] is None:
                change = f"{row['old_rating']} (unrated)"
            else:
                diff = row["new_rating"] - row["old_rating"]
                change = f"{row['old_rating']} -> {row['new_rating']} ({diff:+d})"
            parts += [str(row["perf"]), change]

        print(" | ".join(parts))

    output = render(contest_id, tasks, rows, summary, with_rating)
    print("画像を保存しました:", output)

    if should_post:
        message = f"{build_mentions(rows)}\nお疲れ様でした！"
        if not with_rating:
            message += (
                "（ac-predictor が壊れている影響により、"
                "パフォーマンス及び新レーティングは表示できません）"
            )

        channel_id = os.environ["DISCORD_CHANNEL_ID"]
        thread_id = create_thread(channel_id, contest_id.removeprefix("abc"))
        posted = post_message(thread_id, message, image_path=output, ping=True)
        print("スレッドID:", thread_id, "/ メッセージID:", posted["id"])



if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        detail = traceback.format_exc()[-1500:]
        notify_owner(f"RiPPro-ABC の実行に失敗しました\n```\n{detail}\n```")
        raise