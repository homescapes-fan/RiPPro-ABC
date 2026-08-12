# RiPPro-ABC

AtCoder Beginner Contest (ABC) の終了直後に、RiPPro メンバーの結果を自動で Discord へ投稿する Bot。

今まで手作業で行っていた「スレッドを立てて、順位表のスクリーンショットを撮り、参加者にメンションして『お疲れ様でした！』と投稿」という作業を自動化する。

## 動作

毎週土曜 22:42（ABC 終了の 2 分後）にタスク スケジューラが起動し、以下を実行する。

1. `state.json` に記録された番号 +1 を今回の対象とする
2. AtCoder の順位表を取得し、開催されたかどうかを判定する
3. 参加した RiPPro メンバーを抽出し、perf とレート変化を予測する
4. 順位表を [ac-predictor](https://github.com/key-moon/ac-predictor) を導入した AtCoder と同じ体裁の画像として生成する
5. Discord にコンテスト番号のスレッドを作り、メンション付きで投稿する
6. 成功した場合のみ `state.json` を更新する

### 結果の通知

| 状況 | 通知 |
| --- | --- |
| 開催あり | Discord のチャンネルに投稿 |
| 開催なし | 管理者に DM |
| 失敗 | 管理者に DM（トレースバック付き） |

毎週いずれかが必ず届く。何も届かない場合はタスク自体が起動していないので修正が必要。

## 導入

Python 3.9 以上が必要。

```bash
git clone https://github.com/homescapes-fan/RiPPro-ABC.git
```

```bash
cd RiPPro-ABC
```

```bash
python -m venv .venv
```

```bash
source .venv/Scripts/activate
```

```bash
pip install -r requirements.txt
```

```bash
playwright install chromium
```

最後のコマンドで Chromium 本体（約 150MB）を取得する。`pip install` だけでは動かない。

フォント（`asset/Lato-*.ttf`）はリポジトリに同梱してあるため、別途の導入は不要。

## 設定ファイル

### `.env`

`.env.example` をコピーして値を埋める。Git 管理外。

| 変数 | 取得方法 |
| --- | --- |
| `DISCORD_BOT_TOKEN` | Discord Developer Portal の Bot タブ |
| `DISCORD_CHANNEL_ID` | 投稿先チャンネルを右クリック →「チャンネル ID をコピー」 |
| `ATCODER_SESSION` | ブラウザの開発者ツール → Application → Cookies → `REVEL_SESSION` |
| `OWNER_DISCORD_ID` | 自分の名前を右クリック →「ユーザー ID をコピー」 |

チャンネル ID とユーザー ID のコピーには、Discord の設定で開発者モードを有効にする必要がある。

`ATCODER_SESSION` は**実行のたびに自動更新される**。AtCoder が毎回新しいセッションを返すため、週 1 回動いている限り期限切れは起きない。

### `members.json`

AtCoder ユーザー名と Discord ユーザー ID の対応表。個人情報のため Git 管理外。形式は `members.example.json` を参照。

```json
[
  { "atcoder": "atcoder_id", "discord_id": "123456789012345678" }
]
```

`discord_id` が空の場合はメンションせず AtCoder 名をそのまま表示する。想定外のキー名があると起動時にエラーになる。

### `state.json`

最後に投稿したコンテスト番号を記録する。Git 管理外。

```json
{ "last_contest": "abc470" }
```

投稿に成功したときだけ更新される。開催がなかった週や失敗した週は更新されないため、翌週も同じ番号を試す。ABC が開催されない週（AGC との兼ね合い、年末年始）があってもズレが自動で解消される。

## 実行

### 手動

```bash
python src/main.py
```

`state.json` の次の番号を対象に、表と画像を生成する。**投稿はしない。**

```bash
python src/main.py abc470
```

番号を指定して実行する。この場合 `state.json` は更新されない。

```bash
python src/main.py --post
```

Discord へ投稿する。自動実行と同じ経路。

### 自動

Windows のタスク スケジューラに以下を登録する。

| 項目 | 値 |
| --- | --- |
| トリガー | 週単位・土曜日・22:42 |
| プログラム | `<リポジトリ>\.venv\Scripts\python.exe` |
| 引数 | `<リポジトリ>\src\main.py --post` |
| 開始 | `<リポジトリ>` |
| セキュリティ | ユーザーがログオンしているときのみ実行する |
| 設定 | タスクを停止するまでの時間: 1 時間 |

仮想環境の `python.exe` を直接指定するため、`activate` は不要。

## 運用

### DM が届いたとき

**「今週は ABC が開催されませんでした」** — 実際に開催されていなければ正常。何もしなくてよい。

**トレースバック付きのエラー** — 内容によって対応する。

| 内容 | 対応 |
| --- | --- |
| `JSON が返りませんでした` | `ATCODER_SESSION` を取り直して `.env` を更新 |
| `429 Too Many Requests` | 短時間に実行しすぎ。時間をおいて再実行 |
| Discord API エラー | 権限・チャンネル ID・トークンを確認 |
| その他 | トレースバックの最下部から原因を追う |

原因を直したあと `python src/main.py --post` を実行すれば、その週の分を投稿できる。`state.json` は更新されていないため、番号の指定は不要。

### perf 列が無い投稿が来たとき

ac-predictor が aperf を配信していない週は、perf とレート変化の列を省いた表を投稿し、メッセージに注記を付ける。異常ではなく、その週は AtCoder ユーザー全員が同じ状況になる（例: abc456）。

### メンバーの追加

`members.json` に AtCoder ID と Discord ID を追記する。コンテストに参加していないメンバーは自動的に除外されるため、常時登録しておいてよい。

## 構成

| ファイル | 役割 |
| --- | --- |
| `src/main.py` | 全体の流れ、コンテスト番号の管理 |
| `src/atcoder.py` | AtCoder / ac-predictor からのデータ取得 |
| `src/perf.py` | パフォーマンスの予測 |
| `src/rating.py` | レートの計算 |
| `src/table.py` | 順位表データの整形 |
| `src/render.py` | 順位表の画像生成 |
| `src/discord_post.py` | Discord への投稿・DM |
| `asset/` | Lato フォント（SIL Open Font License、`OFL.txt` 同梱） |

## 予測の仕組み

コンテスト終了直後は AtCoder 公式の perf とレート変化が存在しない（確定は約 30 分後）。表示している値は [ac-predictor](https://github.com/key-moon/ac-predictor) と同じ方式で計算した**予測値**であり、団長が投稿していたスクリーンショットに写っていた数値と一致する。

ac-predictor は計算結果を配信していない。配信しているのは aperf（過去成績の重み付き平均）という材料だけで、perf とレート変化はブラウザ内で計算している。本 Bot はその計算を Python で再実装している。

- 参加者の aperf は ac-predictor が配信するデータを使用（コンテスト開始までに配信される）
- 初参加者の aperf は 1200（資料には 800 とあるが、実測により 1200 で公式と完全一致）
- perf は「その順位を取るのに必要な実力」を二分探索で逆算
- ABC の perf は 2400 で頭打ち
- 同順位のグループには、そのグループが占める位置の平均順位を与える
- 表示時に 400 未満の値を補正する（0 完でも正の数になる）
- レートは過去 perf の重み付き平均から、参加回数による補正を引いて求める
- 1 度も rated 参加していない人（黒）は、名前を `#000000` にし、瓦を表示しない

### 見た目

AtCoder の順位表から実測した値（列幅・余白・行の高さ・配色・フォント）に合わせている。フォントは AtCoder と同じ Lato を同梱し、base64 で HTML に埋め込んで描画する。

## AtCoder への配慮

- 参加者ごとの履歴取得の間に 0.5 秒の待ち時間を入れている（`REQUEST_INTERVAL`）
- 429（レート制限）が返った場合は 5 秒待って 1 回だけ再試行する（`RETRY_WAIT`）
- User-Agent にリポジトリの URL を入れている

開発中に短時間で何度も実行すると 429 を踏むことがある。

## 既知の制限

- 過去のコンテストを指定すると、aperf データが更新されている影響で公式と数点ずれる。最新回では一致する
- 0 完の層では AtCoder の確定値と 10 程度ずれる。 [ac-predictor](https://github.com/key-moon/ac-predictor) に合わせているため、この差はそのまま
- レート 2800 以上のランクアイコン（王冠）の分岐は未検証
- ABC 専用。ARC / AGC を指定すると意図的にエラーで停止する
- 順位表の取得に失敗した週は `state.json` が更新されないため、手動での確認が必要
- 最速正解者の名前の縮小率は AtCoder の実測から逆算した近似値のため、名前によって数 % ずれる