# uranai-app（占い鑑定支援 Web アプリ + MCP）

FastAPI・PostgreSQL・MCP を組み合わせた、占い鑑定支援システムです。

## 現在の実装

### 1. 相談者カルテ
相談者の基本情報を PostgreSQL に保存できます。

### 2. 出生プロフィール
生年月日・出生時間・出生地・タイムゾーンを相談者に紐づけて保存できます。

### 3. 算命学命式
年・月・日干支、十大主星、十二大従星、天中殺などを保存できます。

### 4. 鑑定履歴
相談者1人に対して複数回の鑑定を時系列で保存できます。

保存項目:
- 鑑定日時
- 相談テーマ
- 相談内容
- 使用占術
- 鑑定結果
- アドバイス
- フォロー内容
- 鑑定士用の非公開メモ

REST API:
- `POST /api/clients/{id}/readings` 鑑定履歴を追加
- `GET /api/clients/{id}/readings` 履歴一覧を新しい順に取得
- `GET /api/clients/{id}/readings/{reading_id}` 1件取得
- `PATCH /api/clients/{id}/readings/{reading_id}` 更新
- `DELETE /api/clients/{id}/readings/{reading_id}` 削除

### 5. AI連携用・相談者コンテキスト
AIが鑑定を補助するときに必要な情報を、相談者IDだけでまとめて取得できます。

取得内容:
- 相談者カルテ
- 出生プロフィール（未登録なら `null`）
- 算命学命式（未登録なら `null`）
- 直近の鑑定履歴（既定10件、最大100件）

REST API:
- `GET /api/clients/{id}/context` AI向け統合コンテキスト取得
- `reading_limit` で含める鑑定履歴件数を指定可能

MCP tools:
- `db_now` DB接続確認
- `create_client` 相談者登録
- `search_clients` 相談者検索
- `set_birth_profile` 出生情報の登録・更新
- `get_birth_profile` 出生情報の取得
- `set_sanmeigaku_chart` 算命学命式の登録・更新
- `get_sanmeigaku_chart` 算命学命式の取得
- `add_reading` 鑑定履歴を追加
- `list_readings` 鑑定履歴を新しい順に取得
- `get_client_context` AI鑑定用に相談者情報を一括取得

ブラウザから `/docs` を開くと FastAPI の操作画面で API を試せます。

## 構成
- `web` FastAPI（Web/API/MCP、内部8000番）
- `db` PostgreSQL 16
- `database.py` DB接続・セッション
- `models.py` DBモデル
- `schemas.py` API入力・出力スキーマ
- `server.py` Web API・MCP

## MCP
接続先: `https://<あなたのドメイン>/mcp/sse`

## 今後の実装予定
1. 相談者カルテ ✅
2. 生年月日・出生時間・出生地 ✅
3. 算命学データ・命式 ✅
4. 鑑定履歴 ✅
5. AI連携の拡張 🚧（統合コンテキスト取得まで実装）
6. AI鑑定プロンプト・回答生成
7. 鑑定士向け管理画面
