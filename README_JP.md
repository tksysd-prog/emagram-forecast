# エマグラム予報取得の GitHub Actions 移行手順

## 目的

GAS から Open-Meteo API を直接呼び出すと HTTP 429（日次リクエスト制限）になる問題を避けるため、GitHub Actions が予報を取得し、GAS は GitHub の `forecast.json` を読む構成です。既存の画面 `index.html` と実測スプレッドシート読み取り処理は維持します。

## 同梱ファイル

- `fetch_forecast.py` — Open-Meteo Best Match から予報を取得し `forecast.json` を生成
- `.github/workflows/forecast.yml` — 日本時間 08:00 と 20:00 に実行（GitHub の cron は UTC）
- `Code.gs` — 既存 GAS コードに GitHub 取得関数を追加した版
- `index.html` — 既存画面
- `forecast.json` — 初回実行で生成される。手動で作成する必要はありません

## 1. GitHub リポジトリを用意

1. GitHub で新しい **Public** リポジトリを作成します。例：`emagram-forecast`。
2. ZIP 内のファイルをリポジトリ直下に配置します。`.github/workflows/forecast.yml` の階層を維持してください。
3. `Code.gs` の `GITHUB_FORECAST_RAW_URL` を実際の URL に変更します。例：
   `https://raw.githubusercontent.com/あなたのユーザー名/emagram-forecast/main/forecast.json`
4. `Code.gs` を既存の Apps Script プロジェクトに反映します。HTML ファイル名は `index`（拡張子なし）で登録してください。既存 `index.html` は内容を変更せず置き換え可能です。
5. Apps Script のプロジェクト設定のタイムゾーンを `Asia/Tokyo` にしてください。

> Public リポジトリに置くのは気象予報データのみです。スプレッドシート ID などの既存設定は `Code.gs` にありますが、GitHub に `Code.gs` をアップロードする必要はありません。GAS にだけ設定してください。

## 2. GitHub Actions を実行

1. GitHub リポジトリの **Actions** タブを開きます。
2. `Update emagram forecast` を選び、**Run workflow** を実行します。
3. 実行が成功し、リポジトリ直下に `forecast.json` がコミットされたことを確認します。
4. 次の URL をブラウザで開いて JSON が表示されることを確認します：
   `https://raw.githubusercontent.com/OWNER/REPOSITORY/main/forecast.json`

Open-Meteo 取得が失敗した場合、スクリプトは失敗終了し、既存 `forecast.json` は上書きしません。

## 3. GAS を切り替える

1. `Code.gs` の `GITHUB_FORECAST_RAW_URL` を正しい raw URL に変更して保存します。
2. Apps Script エディタで `testRefreshForecastFromGitHub` を選び、実行して権限を承認します。
3. 実行ログに `ok: true` が出ることを確認します。
4. `installUpdateTriggers` を **一度だけ** 手動実行します。既存の `refreshForecast` トリガーを削除し、`refreshForecastFromGitHub` の 08:00 / 20:00 トリガーを作成して、GitHub から初期データを読み込みます。
5. Web アプリを再読み込みしてグラフを確認します。

## 注意事項

- Apps Script の `refreshForecast()` は旧来の直接 API 取得関数として残していますが、トリガーには使わないでください。今後は `refreshForecastFromGitHub()` を使用します。
- `installUpdateTriggers()` 実行前に、GitHub Actions で `forecast.json` が作成済みである必要があります。
- Apps Script の時間主導型トリガーは指定時刻ちょうどに実行される保証はなく、対象時間帯の中で実行されます。
- GitHub Actions のスケジュールも遅延する場合があります。必要なら Actions タブから手動実行できます。
- 初回の Actions 実行が成功するまでは `forecast.json` はありません。
- GitHub のリポジトリが Private の場合、今回の未認証 raw URL では GAS から読めません。
- Open-Meteo の提供条件・利用制限を守ってください。
