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

REST API:
- `GET /api/clients/{id}/context`

MCP:
- `get_client_context`

### 6. AI鑑定プロンプト・回答生成
保存済み相談者情報を使って、AI鑑定補助用のプロンプトを作成し、OpenAI Responses APIで回答を生成できます。

REST API:
- `POST /api/clients/{id}/ai/prompt` AIへ送るプロンプトを確認
- `POST /api/clients/{id}/ai/generate` AI鑑定補助回答を生成

MCP:
- `build_ai_reading_prompt` AI送信用プロンプトを作成
- `generate_ai_reading` OpenAI APIで回答生成

回答方針:
- 不安を煽らない
- 断定しすぎない
- 保存済み事実と占術上の解釈を区別する
- 過去履歴との矛盾があれば示す
- 最終判断は相談者本人に残す

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
- 今回の相談内容を入力してAI送信前プロンプトを確認
- OpenAI API設定済みの場合はAI鑑定補助回答を生成
- AI鑑定結果をそのまま鑑定履歴の入力フォームへ引き継いで保存

管理画面:
- `GET /admin`

## OpenAI API設定

APIキーはコードやGitHubリポジトリに書き込まず、サーバーの環境変数で設定してください。

```bash
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-5"
```

`OPENAI_API_KEY` が未設定の場合、`/ai/generate` は外部APIを呼ばず `not_configured` を返し、生成予定のプロンプトを確認できます。

Docker Composeではホスト側の `OPENAI_API_KEY` / `OPENAI_MODEL` をWebコンテナへ引き渡します。

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

ブラウザから `/docs` を開くと FastAPI の操作画面で API を試せます。

## 構成
- `web` FastAPI（Web/API/MCP、内部8000番）
- `db` PostgreSQL 16
- `database.py` DB接続・セッション
- `models.py` DBモデル
- `schemas.py` API入力・出力スキーマ
- `ai_service.py` AIプロンプト作成・OpenAI API接続
- `server.py` Web API・MCP
- `admin_ui.py` 鑑定士向け管理画面HTML/JavaScript
- `admin_app.py` `/admin` ルートを追加して既存アプリを拡張

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
9. 認証・権限管理・バックアップ ← 次候補
