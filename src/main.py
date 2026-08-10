import json
import sys
from pathlib import Path

from atcoder import fetch_standings
from table import build_rows

MEMBERS_PATH = Path(__file__).resolve().parent.parent / "members.json"


def load_members():
    """ members.json を読み込みリストで返す"""
    with MEMBERS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def main():
    contest_id = sys.argv[1] if len(sys.argv) > 1 else "abc470"

    members = load_members()
    standings = fetch_standings(contest_id)
    tasks, rows = build_rows(standings, members)

    print(f"{contest_id}: 登録 {len(members)} 人中 {len(rows)} 人が参加")
    print(" | ".join(["順位", "ユーザ", "得点"] + tasks))

    for row in rows:
        score = (
            f"{row['score']}({row['penalty']})" if row["penalty"] else str(row["score"])
        )
        print(" | ".join([str(row["rank"]), row["user"], score] + row["cells"]))


if __name__ == "__main__":
    main()