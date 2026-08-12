"""RiPPro-ABC Bot の入口"""

import json
import sys
import os
import traceback
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


def attach_rating(rows, contest_id):
    """各行にレート変化を追加する"""
    for row in rows:
        history = history_before(fetch_history(row["user"]), contest_id)
        old, new = predict_new_rating(history, row["raw_perf"])

        row["old_rating"] = old
        row["new_rating"] = new if row["is_rated"] else None


def attach_performance(rows, standings, aperfs, contest_id):
    """各行に表示用の perf を追加"""
    aperf_list = collect_aperfs(standings, aperfs, contest_id)
    resolve = rated_rank_resolver(standings)

    for row in rows:
        rated_rank = resolve(row["rank"])
        raw = apply_cap(predict_performance(rated_rank, aperf_list), contest_id)
        row["raw_perf"] = raw
        row["perf"] = display_performanece(raw)

    attach_rating(rows, contest_id)


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
        return

    members = load_members()
    aperfs = fetch_aperfs(contest_id)

    tasks, rows = build_rows(standings, members)
    attach_performance(rows, standings, aperfs, contest_id)
    attach_rating(rows, contest_id)
    summary = build_summary(tasks, rows)

    print(f"{contest_id}: 登録 {len(members)} 人中 {len(rows)} 人が参加")
    print(" | ".join(["順位", "ユーザ", "得点"] + tasks + ["perf", "レート変化"]))

    for index, row in enumerate(rows, start=1):
        cell_texts = [f"{c['score']} {c['time']}".strip() for c in row["cells"]]

        if row["new_rating"] is None:
            change = f"{row['old_rating']} (unrated)"
        else:
            diff = row["new_rating"] - row["old_rating"]
            change = f"{row['old_rating']} -> {row['new_rating']} ({diff:+d})"

        print(
            " | ".join(
                [f"{index}({row['rank']})", row["user"], row["total"]["score"]]
                + cell_texts
                + [str(row["perf"]), change]
            )
        )

    output = render(contest_id, tasks, rows, summary)
    print("画像を保存しました:", output)

    if should_post:
        message = f"{build_mentions(rows)}\nお疲れ様でした！"
        channel_id = os.environ["DISCORD_CHANNEL_ID"]

        thread_id = create_thread(channel_id, contest_id.removeprefix("abc"))
        posted = post_message(thread_id, message, image_path=output, ping=True)
        print("スレッドID:", thread_id, "。メッセージID:", posted["id"])

    if auto and should_post:
        state["last_contest"] = contest_id
        save_state(state)



if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        detail = traceback.format_exc()[-1500:]
        notify_owner(f"RiPPro-ABC の実行に失敗しました\n```\n{detail}\n```")
        raise