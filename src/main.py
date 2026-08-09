import json
import sys
from pathlib import Path

from atcoder import fetch_results

MEMBERS_PATH = Path(__file__).resolve().parent.parent / "members.json"


def load_members():
    """ members.json を読み込みリストで返す"""
    with MEMBERS_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def pick_participants(results, members):
    """コンテスト結果から、メンバー表に載っている人だけを抜き出す"""
    by_name = {row["UserScreenName"]: row for row in results}

    participants = []
    for member in members:
        row = by_name.get(member["atcoder"])
        if row is None:
            continue
        participants.append({"member": member, "result": row})

    participants.sort(key=lambda p: p["result"]["Place"])
    return participants


def main():
    contest_id = sys.argv[1] if len(sys.argv) > 1 else "abc470"

    members = load_members()
    results = fetch_results(contest_id)
    participants = pick_participants(results, members)

    print(f"{contest_id}: 登録 {len(members)} 人中 {len(participants)} 人が参加")
    for p in participants:
        row = p["result"]
        perf = row["Performance"] if row["IsRated"] else "-"
        print(f"{row['Place']:>6}  {row['UserScreenName']:<20} perf={perf}")


if __name__ == "__main__":
    main()