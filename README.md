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

### 10. PostgreSQL自動バックアップ
`backup` コンテナがDB起動後にバックアップを作成し、その後は既定で24時間ごとに圧縮SQLバックアップを保存します。

既定値:
- 保存間隔: 86400秒（24時間）
- 保持期間: 14日
- 保存先: Docker volume `db_backups`
- ファイル形式: `uranai_app_YYYYMMDDTHHMMSSZ.sql.gz`

### 11. 算命学命式の自動計算
出生プロフィールの生年月日から、管理画面の「自動計算」ボタンで命式を作成・更新できます。

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

暦計算は `lunar_python` の節気・干支・十二運を利用し、人体星図の地元は標準的な二十八元（初元・中元・本元）で算出します。節入り当日に出生時刻が登録されている場合はその時刻を使います。出生時刻が不明の節入り当日は正午で暫定計算し、注意メッセージを返します。

既知ケースとして 1977-08-20 の命式が、丁巳・戊申・己酉／中央=司禄星／北=龍高星／東=調舒星／南=石門星／西=鳳閣星／初年=天将星／中年=天恍星／晩年=天貴星になることを回帰テストにしています。

## OpenAI API設定

APIキーはコードやGitHubリポジトリに書き込まず、サーバーの環境変数で設定してください。

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-5"
```

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
- `server.py` Web API・MCP
- `admin_ui.py` 鑑定士向け管理画面HTML/JavaScript
- `admin_app.py` 管理系認証・MCP認証・命式自動計算API
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
12. 算命学命式自動計算 ✅
