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
* { box-sizing: border-box; }
body { margin: 0; background: #ffffff; }
table { border-collapse: collapse; background: #ffffff;
        table-layout: fixed;
        font-family: Lato, "Helvetica Neue", arial, "Noto Sans JP", sans-serif;
        font-size: 14px; color: #333333; }
th, td { border: 1px solid #dddddd; text-align: center;
         white-space: nowrap; vertical-align: middle; line-height: 20px; }
th { padding: 8px 10px 8px 8px; }
td { padding: 4px 6; }
tbody tr:nth-child(odd) { background: #f9f9f9; }
.user { text-align: left; padding: 8px 8px 8px 12px; font-weight: bold; }
.user img { height: 14px; vertical-align: -2px; margin-right: 4px; }
.user .flag { height: 12px; margin-right: 3px; }
.rank { font-weight: 700; }
.score { color: #0000ff; font-weight: 700; font-size: 12.6px; }
.ac { color: #00aa3e; font-weight: 700; font-size: 12.6px; }
.wa { color: #ff0000; font-weight: 400; font-size: 12.6px; }
.time { color: #888888; font-weight: 400; font-size: 12.6px; }
.empty { color: #888888; font-size: 12.6px; }
.up { color: #00aa3e; }
.down { color: #ff0000; }
.flat { color: #888888; }
.muted { color: #888888; }
.summary td { padding: 4px; font-size: 11.2px; color: #888888; background: #ffffff; }
.summary .ac, .summary .time, .summary .empty { font-size: 11.2px; }
.summary .fastest { font-weight: 700; font-size: 10px; line-height: 16px; }
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

    body = ""
    if cell["score"]:
        body += f'<span class="ac">{cell["score"]}</span>'
    if cell["penalty"]:
        body += f'<span class="wa">{cell["penalty"]}</span>'
    if cell["time"]:
        body += f'<div class="time">{cell["time"]}</div>'

    return f"<td>{body}</td>"


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


def fit_font_size(text, width=52.0, base=10.0):
    """幅 width に収まるよう文字サイズを縮める。

    AtCoder の fit-font-size（JavaScript）と同じ挙動を近似する。
    係数 0.55 は実測値から逆算した「1文字あたりの幅 ÷ 文字サイズ」。
    """
    estimated = len(text) * base * 0.55
    if estimated <= width:
        return base
    return round(width / (len(text) * 0.55), 2)


def summary_rows(summary):
    """最速正解者と正解者数の行を返す。"""
    fastest = ""
    counts = ""

    for item in summary:
        if item["user"] is None:
            fastest += '<td class="empty">-</td>'
        else:
            color = rating_color(item["rating"])
            size = fit_font_size(item["user"])
            fastest += (
                f'<td><div class="fastest" '
                f'style="color:{color};font-size:{size}px">'
                f'{html.escape(item["user"])}</div>'
                f'<div class="time">{item["time"]}</div></td>'
            )

        counts += (
            f'<td><span class="ac">{item["accepted"]}</span>'
            f' / <span class="time">{item["tried"]}</span></td>'
        )

    empty = '<td class="empty">-</td><td class="empty">-</td>'
    return (
        f'<tr class="summary"><td colspan="3">最速正解者</td>{fastest}{empty}</tr>'
        f'<tr class="summary"><td colspan="3">'
        '<span class="ac">正解者数</span> / <span class="time">提出者数</span>'
        f"</td>{counts}{empty}</tr>"
    )


def build_html(tasks, rows, summary):
    """順位表の HTML を組み立てる。"""
    head = (
        '<th style="width:49px">順位</th>'
        '<th style="width:303px">ユーザ</th>'
        '<th style="width:60px">得点</th>'
        + "".join(f'<th style="width:60px">{name}</th>' for name in tasks)
        + '<th style="width:84px">perf</th>'
        + '<th style="width:168px">レート変化</th>'
    )

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

        total = row["total"]
        if total["score"] or total["penalty"]:
            total_html = ""
            if total["score"]:
                total_html += f'<span class="score">{total["score"]}</span>'
            if total["penalty"]:
                total_html += f'<span class="wa">{total["penalty"]}</span>'
            if total["time"]:
                total_html += f'<div class="time">{total["time"]}</div>'
        else:
            total_html = '<span class="empty">-</span>'

        body += (
            "<tr>"
            f'<td><div class="rank">{index}</div>'
            f'<div class="time">({row["rank"]})</div></td>'
            f'<td class="user" style="color:{color}">{images}'
            f'{html.escape(row["user"])}</td>'
            f"<td>{total_html}</td>"
            + "".join(task_cell(cell) for cell in row["cells"])
            + f'<td class="score" style="color:{rating_color(row["perf"])}">'
            f'{row["perf"]}</td>'
            f"<td>{rating_cell(row)}</td>"
            "</tr>"
        )

    return (
        f"<style>{STYLE}</style><table>"
        f"<thead><tr>{head}</tr></thead>"
        f"<tbody>{body}{summary_rows(summary)}</tbody></table>"
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