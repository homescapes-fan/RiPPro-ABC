"""順位表のデータを、表示用の形に整える。"""

def format_elapsed(nanoseconds):
    """ナノ秒を分:秒の文字列にする。"""
    seconds = nanoseconds // 1_000_000_000
    return f"{seconds // 60}:{seconds % 60:02d}"


def format_task_result(result):
    """1問分の結果を、順位表のセル1つ分に整える。"""
    if result is None:
        return {
            "score": "",
            "penalty": "",
            "time": "",
            "elapsed": None,
            "solved": False,
            "tried": False,
            }

    score = result["Score"] // 100
    if score > 0:
        penalty = result["Penalty"]
        return {
            "score": str(score),
            "penalty": f"({penalty})" if penalty else "",
            "time": format_elapsed(result["Elapsed"]),
            "elapsed": result["Elapsed"],
            "solved": True,
            "tried": True,
        }

    return {
        "score": "",
        "penalty": f"({result['Failure']})",
        "time": "",
        "elapsed": None,
        "solved": False,
        "tried": True,
    }


def format_total(total):
    """得点欄の表示を決める。"""
    if total["Count"] == 0:
        return {"score": "-", "penalty": "", "time": ""}

    score = total["Score"] // 100
    if score == 0:
        return {"score": "", "penalty": "(0)", "time": ""}
    
    penalty = total["Penalty"]
    return {
        "score": str(score),
        "penalty": f"({penalty})" if penalty else "",
        "time": format_elapsed(total["Elapsed"]),
    }

def build_summary(tasks, rows):
    """各問題の最速正解者と、正解者数・提出者数を求める。"""
    summary = []

    for index, name in enumerate(tasks):
        cells = [row["cells"][index] for row in rows]
        solved = [
            (cell["elapsed"], row["user"], cell["time"])
            for row, cell in zip(rows, cells)
            if cell["solved"]
        ]

        fastest = min(solved) if solved else None
        summary.append(
            {
                "task": name,
                "user": fastest[1] if fastest else None,
                "time": fastest[2] if fastest else None,
                "accepted": len(solved),
                "tried": sum(1 for cell in cells if cell["tried"]),
            }
        )

    return summary


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
                "total": format_total(total),
                "cells": [
                    format_task_result(raw["TaskResults"].get(task_key_of[name]))
                    for name in tasks
                ],
                "is_rated": raw["IsRated"],
                "country": raw["Country"],
                "atcoder_rank": raw["AtCoderRank"],
            }
        )

    rows.sort(key=lambda row: row["rank"])
    return tasks, rows