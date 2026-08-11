import json
import os

from openai import OpenAI

DEFAULT_MODEL = os.environ.get("OPENAI_MODEL", "gpt-5")

SYSTEM_INSTRUCTIONS = """あなたは占い師の鑑定を補助するAIです。
相談者の不安を煽らず、断定しすぎず、本人の選択を尊重してください。
保存済みの事実と、占術上の解釈・推測を明確に分けてください。
過去の鑑定履歴との一貫性を確認しつつ、矛盾があれば隠さず示してください。
回答は日本語で、次の順に簡潔かつ実用的にまとめてください。
1. 今回の相談の要点
2. 命式・出生情報・過去履歴から見えるポイント
3. 現時点での見立て
4. 注意すべき別の可能性
5. 相談者が次に取れる行動
医療・法律・金融など高リスク分野では、占いを専門家判断の代替にしないでください。"""


def build_reading_prompt(context: dict, question: str) -> str:
    safe_context = json.dumps(context, ensure_ascii=False, indent=2)
    return f"""以下は相談者について保存されている情報です。

--- 相談者コンテキスト ---
{safe_context}
--- ここまで ---

今回の相談・質問:
{question}

保存情報にないことを事実として作らず、占術上の解釈は解釈として示してください。"""


def generate_reading(context: dict, question: str, model: str | None = None) -> dict:
    if not question.strip():
        raise ValueError("question is required")

    api_key = os.environ.get("OPENAI_API_KEY")
    selected_model = model or DEFAULT_MODEL
    prompt = build_reading_prompt(context, question)

    if not api_key:
        return {
            "status": "not_configured",
            "model": selected_model,
            "message": "OPENAI_API_KEY is not configured",
            "prompt": prompt,
        }

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model=selected_model,
        instructions=SYSTEM_INSTRUCTIONS,
        input=prompt,
    )
    return {
        "status": "completed",
        "model": selected_model,
        "response_id": response.id,
        "answer": response.output_text,
    }
