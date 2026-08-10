"""順位表のデータを、表示用の形に整える。"""

def format_elapsed(nanoseconds):
    """ナノ秒を分:秒の文字列にする。"""
    seconds = nanoseconds // 1_000_000_000
    return f"{seconds // 60}:{seconds % 60:02d}"

def format_task_result(result):
    """1問分の結果を、順位表のセル1つ分の文字列にする・"""
    if result is None:
        return ""

    score = result["Score"] // 100
    if score > 0:
        penalty = result["Penalty"]
        head = f"{score}({penalty})" if penalty else str(score)
        return f"{head} {format_elapsed(result['Elapsed'])}"

    tries = result["Failure"]
    return f"({tries})" if tries else ""

def build_rows(standings, members):
    """順位表から、メンバーの行だけを取り出して表示用に整える。"""
    tasks = [task["Assignment"] for task in standings["TaskInfo"]]
    task_key_of = {
        task["Assignment"]: task["TaskScreenName"] for task in standings["TaskInfo"]
    }
    row_of = {row["UserScreenName"]: row for row in standings["StandingsData"]}

    rows = []
    for member in members:
        raw = row_of.get(member["atcoder"])
        if raw is None:
            continue

        total = raw["TotalResult"]
        rows.append(
            {
                "member": member,
                "rank": raw["Rank"],
                "user": raw["UserScreenName"],
                "deleted": raw["UserIsDeleted"],
                "score": total["Score"] // 100,
                "penalty": total["Penalty"],
                "elapsed": format_elapsed(total["Elapsed"]),
                "cells": [
                    format_task_result(raw["TaskResults"].get(task_key_of[name]))
                    for name in tasks
                ],
            }
        )

    rows.sort(key=lambda row: row["rank"])
    return tasks, rows