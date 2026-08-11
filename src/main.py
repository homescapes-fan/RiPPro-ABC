"""RiPPro-ABC Bot の入口"""

import json
import sys
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from atcoder import fetch_aperfs, fetch_history, fetch_standings, history_before
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
from discord_post import post_message

MEMBERS_PATH = Path(__file__).resolve().parent.parent / "members.json"


def load_members():
    """ members.json を読み込みリストで返す"""
    with MEMBERS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


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
    contest_id = sys.argv[1] if len(sys.argv) > 1 else "abc470"
    should_post = "--post" in sys.argv

    members = load_members()
    print(members[0])
    standings = fetch_standings(contest_id)
    aperfs = fetch_aperfs(contest_id)

    tasks, rows = build_rows(standings, members)
    attach_performance(rows, standings, aperfs, contest_id)

    print(f"{contest_id}: 登録 {len(members)} 人中 {len(rows)} 人が参加")
    print(" | ".join(["順位", "ユーザ", "得点"] + tasks + ["perf", "レート変化"]))

    for index, row in enumerate(rows, start=1):
        if row["new_rating"] is None:
            change = f"{row['old_rating']} (unrated)"
        else:
            diff = row["new_rating"] - row["old_rating"]
            change = f"{row['old_rating']} -> {row['new_rating']} ({diff:+d})"
            cell_texts = [f"{c['score']} {c['time']}".strip() for c in row["cells"]]

        print(row["user"], "AtCoderRank =", row["atcoder_rank"])
        print(
            " | ".join(
                [f"{index}({row['rank']})", row["user"], row["total"]["score"]]
                + cell_texts
                + [str(row["perf"]), change]
            )
        )

    summary = build_summary(tasks, rows)
    output = render(contest_id, tasks, rows, summary)
    print("画像を保存しました:", output)

    if should_post:
        message = f"{build_mentions(rows)}\nお疲れ様でした！"
        posted = post_message(
            os.environ["DISCORD_CHANNEL_ID"], message, image_path=output, ping=True
        )
        print("投稿しました。メッセージID:", posted["id"])



if __name__ == "__main__":
    main()