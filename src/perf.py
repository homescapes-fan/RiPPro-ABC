# 過去回では公式と 1〜10 ほどずれる（aperf ファイルが後から更新されている影響か）。
# 最新回では完全一致するため、実運用では問題にならないと判断して未対応。
"""パフォーマンスの予測"""
import math

# 初参加者に用いる aperf（検索では ABC=800だったが、実際には1200）
CENTER_APERF = 1200

# ABC の perf 上限
ABC_PERFORMANCE_CAP = 2400


def center_aperf(contest_id):
    """初参加者に割り当てる aperf を、コンテストIDの接頭辞から決める。"""
    if not contest_id.startswith("abc"):
        raise ValueError(f"ABC 以外では未検証です: {contest_id}")
    return CENTER_APERF

def apply_cap(performance, contest_id):
    """ABCの perf 上限を適用"""
    if contest_id.startswith("abc"):
        return min(performance, ABC_PERFORMANCE_CAP)
    return performance


def collect_aperfs(standings, aperfs, contest_id, fallback=None):
    """rated 参加者全員の aperf を並べたリストを作成"""
    if fallback is None:
        fallback = center_aperf(contest_id)
    return [
        aperfs.get(row["UserScreenName"], fallback)
        for row in standings["StandingsData"]
        if row["IsRated"]
    ]

def rated_ranks(standings, tie="mid"):
    """rated 参加者だけで数えなおした順位を ユーザー名 -> 順位 で返す。

       tie は同順位グループの扱い
         "best"  … グループ先頭の順位を全員に与える（AtCoderの表示と同じ）
         "worst" … グループ末尾の順位を全員に与える
         "mid"   … 先頭と末尾の中間
    """
    rated = [row for row in standings["StandingsData"] if row["IsRated"]]
    rated.sort(key=lambda row: row["Rank"])

    ranks = {}
    start = 0

    while start < len(rated):
        end = start
        while end + 1 < len(rated) and rated[end + 1]["Rank"] == rated[start]["Rank"]:
            end += 1

        best = start + 1
        worst = end + 1
        if tie == "best":
            value = best
        elif tie == "worst":
            value = worst
        else:
            value = (best + worst) / 2

        for row in rated[start : end + 1]:
            ranks[row["UserScreenName"]] = value

        start = end + 1

    return ranks

def positivize(value):
    """400 未満の値を、AtCoder の表示に合わせて正の範囲に押し込める。"""
    if value >= 400.0:
        return value
    return 400.0 / math.exp((400.0 - value) / 400.0)

def display_performanece(raw_performance):
    """順位表に対応する perf を返す。"""
    return round(positivize(raw_performance))

def expected_rank(strength, aperf_list):
    """実力 strength の人が取るであろう順位（期待値）を返す。"""
    return sum(
        1.0 / (1.0 + 6.0 ** ((strength - aperf) / 400.0)) for aperf in aperf_list
    )

def predict_performance(rank, aperf_list):
    """順位 rank を取るのに必要な実力（perf）を二分探索で求める。"""
    low, high = -10000.0, 10000.0

    for _ in range(60):
        mid = (low + high) / 2
        if expected_rank(mid, aperf_list) < rank - 0.5:
            high = mid
        else:
            low = mid

    return round((low + high) / 2)