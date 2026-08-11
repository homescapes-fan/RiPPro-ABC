"""順位表を画像にする。"""

import html
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT_DIR = Path(__file__).resolve().parent.parent / "out"

# AtCoder のレート帯の色（上限, 色）
RATING_BANDS = [
    (400, "gray", "#808080"),
    (800, "brown", "#804000"),
    (1200, "green", "#008000"),
    (1600, "cyan", "#00c0c0"),
    (2000, "blue", "#0000ff"),
    (2400, "yellow", "#c0c000"),
    (2800, "orange", "#ff8000"),
]

TOP_BAND =("red", "#ff0000")

CROWNS = [
    (1, "crown_champion"),
    (10, "crown_gold"),
    (30, "crown_silver"),
    (100, "crown_bronze"),
]

STYLE = """
body { margin: 0; background: #ffffff; }
table { border-collapse: collapse;
         font-family: "Yu Gothic UI", "Meiryo", sans-serif; font-size; 13px; }
th, td { border: 1px solid #dddddd; padding: 4px 10px;
         text-align: center; white-space: nowrap; }
th { background: #f5f5f5; }
.user { text-align: left; font-weight: bold; }
.value { font-weight: bold; }
.time { color: #888888; font-size: 11px; }
.solved .value { color: #008000; }
.failed .value { color: #dd0000; }
.empty { color: #cccccc; }
.up { color: #0080000; }
.down { color: #dd0000; }
.flat { color: #888888; }
.muted { color: #888888; }
.summary td { background: #fafafa; }
.user img { height: 14px; vertical-align: -2px; margin-right: 4px; }
.user .flag { height: 12px; margin-right: 3px; }
"""

def flag_url(country):
    """国旗画像の URL を探す。国が未設定なら None """
    if not country:
        return None
    return f"https://img.atcoder.jp/assets/flag/{country}.png"


def rating_band(value):
    """レート帯の（名前，色）を返す。"""
    for upper, name, color in RATING_BANDS:
        if value < upper:
            return name, color
    return TOP_BAND


def rating_color(value):
    """レート帯に対応する色を返す。"""
    return rating_band(value)[1]


def user_icon_url(rating, atcoder_rank):
    """ユーザー名の左の瓦または王冠のURLを返す。無い場合はNone"""
    if atcoder_rank:
        for limit, name in CROWNS:
            if atcoder_rank <= limit:
                return f"https://img.atcoder.jp/assets/icon/{name}.png"

    if rating >= 2800:
        return None

    band, _ = rating_band(rating)
    level = (rating % 400) // 100 + 1
    return f"https://img.atcoder.jp/assets/user/user-{band}-{level}.png"


def task_cell(cell):
    """問題1つ分のセルの HTML を返す。"""
    if not cell["tried"]:
        return '<td class="empty">-</td>'

    body = f'<div class="time">{cell["score"]}</div>'
    if cell["time"]:
        body += f'<div class="time">{cell["time"]}</div>'

    css_class = "solved" if cell["solved"] else "failed"
    return f'<td class="{css_class}">{body}</td>'


def rating_cell(row):
    """レート変化のセルの中身を返す。"""
    old = row["old_rating"]

    if row["new_rating"] is None:
        return (
            f'<span style="color:{rating_color(old)}">{old}</span>'
            '<span class="muted">(unrated)</span>'
        )

    new = row["new_rating"]
    diff = new - old
    sign = "up" if diff > 0 else "down" if diff < 0 else "flat"
    return (
        f'<span style="color:{rating_color(old)}">{old}</span>'
        f' →<span style="color:{rating_color(new)}">{new}</span>'
        f'<span class="sign">({diff:+d})</span>'
    )


def summary_rows(summary):
    """最速正解者と正解者数の行を返す。"""
    fastest = ""
    counts = ""

    for item in summary:
        if item["user"] is None:
            fastest += '<td class="empty">-</td>'
        else:
            fastest += (
                f'<td><div class="time">{html.escape(item["user"])}</div>'
                f'<div class="time">{item["time"]}</div></td>'
            )
        counts += f'<td class="time">{item["accepted"]}/{item["tried"]}</td>'

    empty = '<td class="empty">-</td><td class="empty">-</td>'
    return (
        f'<tr class="summary"><td colspan="3">最速正解者</td>{fastest}{empty}</tr>'
        f'<tr class="summary"><td colspan="3">正解者数/提出者数</td>{counts}{empty}</tr>'
    )


def build_html(tasks, rows, summary):
    """順位表の HTML を組み立てる。"""
    headers = ["順位", "ユーザ", "得点"] + tasks + ["perf", "レート変化"]
    head = "".join(f"<th>{name}</th>" for name in headers)

    body = ""
    for index, row in enumerate(rows, start=1):
        color = rating_color(row["old_rating"])
        images = ""
        flag = flag_url(row["country"])
        if flag:
            images += f'<img class="flag" src="{flag}">'

        icon = user_icon_url(row["old_rating"], row["atcoder_rank"])
        if icon:
            images += f'<img src="{icon}">'

        body += (
            "<tr>"
            f'<td><div class="value">{index}</div>'
            f'<div class="time">({row["rank"]})</div></td>'
            f'<td class="user" style="color:{color}">{images}'
            f'{html.escape(row["user"])}</td>'
            f'<td><div class="value">{row["total"]["score"]}</div>'
            f'<div class="time">{row["total"]["time"]}</div></td>'
            + "".join(task_cell(cell) for cell in row["cells"])
            + f'<td class="value" style="color:{rating_color(row["perf"])}">'
            f'{row["perf"]}</td>'
            f"<td>{rating_cell(row)}</td>"
            "</tr>"
        )

    return (
        f"<style>{STYLE}</style><table><tr>{head}</tr>"
        f"{body}{summary_rows(summary)}</table>"
        )


def render(contest_id, tasks, rows, summary):
    """順位表の画像を作り、保存先のパスを返す。"""
    OUT_DIR.mkdir(exist_ok=True)
    output = OUT_DIR / f"{contest_id}.png"

    document = build_html(tasks, rows, summary)
    (OUT_DIR / "preview.html").write_text(document, encoding="utf-8")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        page = browser.new_page(device_scale_factor=2)
        page.set_content(document, wait_until="networkidle")
        page.locator("table").screenshot(path=str(output))
        browser.close()

    return output