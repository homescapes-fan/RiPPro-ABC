"""順位表を画像にする。"""

import html
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT_DIR = Path(__file__).resolve().parent.parent / "out"

# AtCoder のレート帯の色（上限, 色）
