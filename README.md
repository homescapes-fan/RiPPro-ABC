# RiPPro-ABC

AtCoder Beginner Contest (ABC) の終了後に、RiPPro メンバーの結果を自動で Discord へ投稿する Bot です。

## やること

1. ABC の終了を検知する
2. 参加したメンバーの順位・perf・レート変化を AtCoder から取得する
3. 順位表を画像にする
4. 参加者にメンションを付けて Discord へ投稿する

## 構成（予定）

- `src/atcoder.py` … AtCoder からデータを取得
- `src/render.py` … 順位表を画像化
- `src/discord_post.py` … Discord へ投稿
- `src/main.py` … 全体の流れ
- `members.json` … AtCoder ユーザ名 と Discord ユーザー ID の対応表

## 開発状況

準備中