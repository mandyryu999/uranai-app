# uranai-app（占い鑑定支援 Web アプリ + MCP）

FastAPI・PostgreSQL・MCP を組み合わせた、占い鑑定支援システムです。

## 現在の実装

### 1. 相談者カルテ
相談者の基本情報を PostgreSQL に保存できます。

保存項目:
- 氏名
- ふりがな
- 電話番号
- メールアドレス
- LINE名
- メモ

REST API:
- `POST /api/clients` 新規登録
- `GET /api/clients` 一覧・検索
- `GET /api/clients/{id}` 詳細
- `PATCH /api/clients/{id}` 更新
- `DELETE /api/clients/{id}` 削除

### 2. 出生プロフィール
相談者1人につき1件の出生情報を保存できます。

保存項目:
- 生年月日
- 出生時間
- 出生時間不明フラグ
- 出生都道府県
- 出生市区町村
- 出生地詳細
- タイムゾーン（既定: `Asia/Tokyo`）

REST API:
- `POST /api/clients/{id}/birth-profile` 新規登録
- `GET /api/clients/{id}/birth-profile` 取得
- `PATCH /api/clients/{id}/birth-profile` 更新
- `DELETE /api/clients/{id}/birth-profile` 削除

MCP tools:
- `db_now` DB接続確認
- `create_client` 相談者登録
- `search_clients` 相談者検索
- `set_birth_profile` 出生情報の登録・更新
- `get_birth_profile` 出生情報の取得

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
3. 算命学データ・命式 ← 次
4. 鑑定履歴
5. AI連携の拡張
6. 鑑定士向け管理画面
