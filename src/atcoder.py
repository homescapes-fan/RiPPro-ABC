"""AtCoderから結果を取得"""

import sys

import requests

USER_AGENT = "RiPPro-ABC-Bot(https://github.com/homescapes-fan/RiPPro-ABC)"

def fetch_results(contest_id):
    """指定したコンテストの全参加者の結果を取得し、リストで返す"""
    url = f"https://atcoder.jp/contests/{contest_id}/results/json"
    response = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=10)
    response.raise_for_status()
    return response.json()


def main():
    contest_id = sys.argv[1] if len(sys.argv) > 1 else "abc469"

    results = fetch_results(contest_id)
    print(f"{contest_id}: {len(results)} 件の結果を取得しました")

    for row in results[:5]:
        print(
            row["Place"],
            row["UserScreenName"],
            f"perf={row['Performance']}",
            f"{row['OldRating']} -> {row['NewRating']}",
            f"rated={row['IsRated']}"
        )

if __name__ == "__main__":
    main()