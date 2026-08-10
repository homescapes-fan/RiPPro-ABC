"""RiPPro-ABC Bot の入口"""

import json
import sys
from pathlib import Path

from atcoder import fetch_aperfs, fetch_standings
from perf import (
    apply_cap,
    collect_aperfs,
    display_performanece,
    predict_performance,
    rated_rank_resolver,
)
from table import build_rows

MEMBERS_PATH = Path(__file__).resolve().parent.parent / "members.json"


def load_members():
    """ members.json を読み込みリストで返す"""
    with MEMBERS_PATH.open(encoding="utf-8") as f:
        return json.load(f)

def attach_performance(rows, standings, aperfs, contest_id):
    """各行に表示用の perf を追加"""
    aperf_list = collect_aperfs(standings, aperfs, contest_id)
    resolve = rated_rank_resolver(standings)

    for row in rows:
        rated_rank = resolve(row["rank"])
        raw = apply_cap(predict_performance(rated_rank, aperf_list), contest_id)
        row["perf"] = display_performanece(raw)


def main():
    contest_id = sys.argv[1] if len(sys.argv) > 1 else "abc470"

    members = load_members()
    standings = fetch_standings(contest_id)
    aperfs = fetch_aperfs(contest_id)

    tasks, rows = build_rows(standings, members)
    attach_performance(rows, standings, aperfs, contest_id)

    print(f"{contest_id}: 登録 {len(members)} 人中 {len(rows)} 人が参加")
    print(" | ".join(["順位", "ユーザ", "得点"] + tasks + ["perf"]))

    for index, row in enumerate(rows, start=1):
        score = (
            f"{row['score']}({row['penalty']})" if row["penalty"] else str(row["score"])
        )
        print(
            " | ".join(
                [f"{index}({row["rank"]})", row["user"], score]
                + row["cells"]
                + [str(row["perf"])]
            )
        )


if __name__ == "__main__":
    main()