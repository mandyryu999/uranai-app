# uranai-app（占い鑑定支援 Web アプリ + MCP）

FastAPI・PostgreSQL・MCP・OpenAI API を組み合わせた、占い鑑定支援システムです。

## 現在できること

### 1. 相談者カルテ
相談者の基本情報を PostgreSQL に保存・検索・編集できます。

### 2. 出生プロフィール
生年月日・出生時間・出生地・タイムゾーンを相談者に紐づけて保存できます。

### 3. 算命学命式
年・月・日干支、十大主星、十二大従星、天中殺などを保存・編集できます。

### 4. 鑑定履歴
相談者1人に対して複数回の鑑定を時系列で保存できます。

### 5. AI連携
相談者カルテ、出生情報、算命学命式、過去の鑑定履歴をまとめてAIへ渡し、OpenAI Responses APIで鑑定補助回答を生成できます。

### 6. 鑑定士向け管理画面
`/admin` から次の操作を行えます。

- 氏名・LINE名などで相談者検索
- 新規相談者登録
- 相談者カルテ編集
- 出生情報の登録・編集
- 算命学命式の登録・編集
- 命式の自動計算
- 十大主星を人体星図に近い配置で確認
- 鑑定履歴の追加・確認
- AI送信前プロンプト確認
- AI鑑定補助回答の生成
- AI鑑定結果を鑑定履歴へ保存

### 7. 初期管理者作成・ログイン
管理者がまだ1人もいない場合は、トップURLから `/setup` に移動し、アプリ画面だけで最初の管理者を作成できます。

- `/login` から管理者ID・パスワードでログイン
- ログイン状態は12時間保持
- `/logout` でログアウト
- パスワードはPBKDF2-HMAC-SHA256 + ランダムソルトでハッシュ保存
- 元のパスワード文字列はDBへ保存しない

### 8. 管理者設定
`/settings/admin` から管理者アカウントを管理できます。

- 登録済み管理者一覧を確認
- 2人目以降の管理者を追加
- 自分のパスワードを変更
- パスワード変更時は現在のパスワード確認が必須
- 変更後はいったんログアウトして再ログイン

現時点では登録された管理者は全員同じ権限です。

### 9. OpenAI API設定
`/settings/openai` からOpenAI APIキーを登録・更新・削除できます。

- GitHub Secretsを操作しなくてもアプリ内で設定可能
- APIキーはDBへ平文保存せずFernet暗号化
- 暗号鍵はDocker volume `app_secrets` に永続保存
- 保存後はキー全文を再表示せずマスク表示のみ
- アプリ内キーが未登録の場合のみ `OPENAI_API_KEY` 環境変数へフォールバック

### 10. MCPトークン認証
MCP接続は管理画面とは別のBearerトークンで保護します。

```text
Authorization: Bearer <MCP_AUTH_TOKEN>
```

### 11. PostgreSQL自動バックアップ
`backup` コンテナがDB起動後にバックアップを作成し、その後は既定で24時間ごとに圧縮SQLバックアップを保存します。

- 保存間隔: 86400秒（24時間）
- 保持期間: 14日
- 保存先: Docker volume `db_backups`
- ファイル形式: `uranai_app_YYYYMMDDTHHMMSSZ.sql.gz`

### 12. 算命学命式の自動計算
出生プロフィールの生年月日から命式を作成・更新できます。

自動計算対象:
- 年干支・月干支・日干支
- 十大主星（中央・北方・東方・南方・西方）
- 十二大従星（初年期・中年期・晩年期）
- 天中殺
- 二十八元で選択した蔵干と節入り日数の計算メモ

REST API:
- `POST /api/clients/{id}/sanmeigaku-chart/auto-calculate`

MCP:
- `auto_calculate_sanmeigaku`

節入り当日に出生時刻が登録されている場合はその時刻を使います。出生時刻が不明の節入り当日は正午で暫定計算し、注意メッセージを返します。

## 主なMCP tools
- `db_now`
- `create_client`
- `search_clients`
- `set_birth_profile`
- `get_birth_profile`
- `set_sanmeigaku_chart`
- `get_sanmeigaku_chart`
- `auto_calculate_sanmeigaku`
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
- `sanmeigaku_engine.py` 命式自動計算エンジン
- `ai_service.py` AIプロンプト作成・OpenAI API接続
- `secure_settings.py` APIキー暗号化保存
- `server.py` Web API・MCP
- `admin_ui.py` 鑑定士向け管理画面
- `admin_app.py` 管理者認証・設定・MCP認証・命式自動計算API
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
9. 初期管理者作成・ログイン ✅
10. OpenAI APIキーのアプリ内設定 ✅
11. 管理者追加・パスワード変更 ✅
12. MCPトークン認証 ✅
13. PostgreSQL自動バックアップ ✅
14. 算命学命式自動計算 ✅
