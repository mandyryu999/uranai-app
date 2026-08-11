# uranai-app（占い鑑定支援 Web アプリ + MCP）

FastAPI・PostgreSQL・MCP・OpenAI API を組み合わせた、占い鑑定支援システムです。

## 現在の実装

### 1. 相談者カルテ
相談者の基本情報を PostgreSQL に保存できます。

### 2. 出生プロフィール
生年月日・出生時間・出生地・タイムゾーンを相談者に紐づけて保存できます。

### 3. 算命学命式
年・月・日干支、十大主星、十二大従星、天中殺などを保存できます。

### 4. 鑑定履歴
相談者1人に対して複数回の鑑定を時系列で保存できます。

### 5. AI連携用・相談者コンテキスト
相談者カルテ、出生情報、算命学命式、直近の鑑定履歴を1回で取得できます。

### 6. AI鑑定プロンプト・回答生成
保存済み相談者情報を使って、AI鑑定補助用のプロンプトを作成し、OpenAI Responses APIで回答を生成できます。

### 7. 鑑定士向け管理画面
ブラウザから `/admin` を開くと、相談者の登録から鑑定履歴保存まで一連の作業を行えます。

できること:
- 氏名・LINE名などで相談者検索
- 新規相談者登録
- 相談者カルテ編集
- 出生情報の登録・編集
- 算命学命式の登録・編集
- 十大主星を人体星図に近い配置で確認
- 新しい鑑定履歴を保存
- 直近の鑑定履歴を確認
- AI送信前プロンプトを確認
- AI鑑定補助回答を生成
- AI鑑定結果を鑑定履歴へ引き継いで保存

### 8. 管理画面・管理API認証
HTTP Basic認証で `/admin`、`/api/...`、`/docs`、`/openapi.json` を保護します。`/health` はデプロイ・死活監視用として公開のままです。

```bash
export ADMIN_USERNAME="your-admin-name"
export ADMIN_PASSWORD="十分に長いランダムなパスワード"
```

認証情報が未設定の場合、保護対象は503を返して閉じます。

### 9. MCPトークン認証
MCP接続は管理画面とは別のBearerトークンで保護します。

```bash
export MCP_AUTH_TOKEN="十分に長いランダムなトークン"
```

MCPクライアントは接続時に次のHTTPヘッダーを送ってください。

```text
Authorization: Bearer <MCP_AUTH_TOKEN>
```

`MCP_AUTH_TOKEN` が未設定の場合、`/mcp...` は503を返して閉じます。間違ったトークンやトークンなしの場合は401です。

### 10. PostgreSQL自動バックアップ
`backup` コンテナがDB起動後にバックアップを作成し、その後は既定で24時間ごとに圧縮SQLバックアップを保存します。

既定値:
- 保存間隔: 86400秒（24時間）
- 保持期間: 14日
- 保存先: Docker volume `db_backups`
- ファイル形式: `uranai_app_YYYYMMDDTHHMMSSZ.sql.gz`

必要に応じて変更できます。

```bash
export BACKUP_INTERVAL_SECONDS=86400
export BACKUP_RETENTION_DAYS=14
```

手動バックアップ:

```bash
docker compose exec backup /bin/sh /backup.sh
```

バックアップ一覧確認:

```bash
docker compose exec backup ls -lh /backups
```

復元する場合は、対象の `.sql.gz` を展開して `psql` に流し込みます。復元操作は既存データを上書きする可能性があるため、実行前に必ず別バックアップを取得してください。

## OpenAI API設定

APIキーはコードやGitHubリポジトリに書き込まず、サーバーの環境変数で設定してください。

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-5"
```

`OPENAI_API_KEY` が未設定の場合、`/ai/generate` は外部APIを呼ばず `not_configured` を返し、生成予定のプロンプトを確認できます。

## 主なMCP tools
- `db_now`
- `create_client`
- `search_clients`
- `set_birth_profile`
- `get_birth_profile`
- `set_sanmeigaku_chart`
- `get_sanmeigaku_chart`
- `add_reading`
- `list_readings`
- `get_client_context`
- `build_ai_reading_prompt`
- `generate_ai_reading`

## 構成
- `web` FastAPI（Web/API/MCP、内部8000番）
- `db` PostgreSQL 16
- `backup` PostgreSQLバックアップ用サイドカー
- `database.py` DB接続・セッション
- `models.py` DBモデル
- `schemas.py` API入力・出力スキーマ
- `ai_service.py` AIプロンプト作成・OpenAI API接続
- `server.py` Web API・MCP
- `admin_ui.py` 鑑定士向け管理画面HTML/JavaScript
- `admin_app.py` 管理系Basic認証とMCP Bearer認証
- `scripts/backup.sh` PostgreSQLバックアップ処理

## MCP
接続先: `https://<あなたのドメイン>/mcp/sse`

## 実装ロードマップ
1. 相談者カルテ ✅
2. 生年月日・出生時間・出生地 ✅
3. 算命学データ・命式 ✅
4. 鑑定履歴 ✅
5. AI向け統合コンテキスト ✅
6. AI鑑定プロンプト・回答生成 ✅
7. 鑑定士向け管理画面 ✅
8. 管理画面から登録・編集・保存 ✅
9. 管理画面・管理API認証 ✅
10. MCPトークン認証 ✅
11. PostgreSQL自動バックアップ ✅
