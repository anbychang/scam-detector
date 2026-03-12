"""AI 語意分析模組 — 用 Groq 免費 API 呼叫 LLM"""
import json
import os
from groq import Groq

SYSTEM_PROMPT = """你是一個台灣防詐騙專家。使用者會給你一段可疑訊息，請分析是否為詐騙。

請用以下 JSON 格式回覆（不要加任何其他文字）：

{
  "is_scam": true/false,
  "confidence": 0-100,
  "scam_type": "詐騙類型名稱（如：假投資詐騙、感情詐騙、假冒政府、求職詐騙、購物詐騙、釣魚詐騙）或 '非詐騙'",
  "explanation": "用白話文解釋這段訊息哪裡有問題，為什麼判斷是/不是詐騙（2-3句話）",
  "red_flags": ["可疑點1", "可疑點2", "可疑點3"],
  "advice": "建議使用者怎麼做（1-2句話）"
}

注意：
- 你的判斷要保守，寧可多警告也不要漏掉詐騙
- 用繁體中文回覆
- 考慮台灣常見的詐騙手法
- 如果是正常訊息就如實說，不要硬扯成詐騙
"""


def ai_analyze(text: str, api_key: str) -> dict:
    """用 LLM 分析訊息是否為詐騙"""
    client = Groq(api_key=api_key)

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"請分析以下訊息是否為詐騙：\n\n{text}"},
        ],
        temperature=0.1,
        max_tokens=800,
    )

    raw = response.choices[0].message.content.strip()

    # 嘗試解析 JSON
    try:
        # 處理可能的 markdown code block
        if "```" in raw:
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw)
    except json.JSONDecodeError:
        # 如果解析失敗，回傳基本結構
        result = {
            "is_scam": None,
            "confidence": 0,
            "scam_type": "分析失敗",
            "explanation": raw,
            "red_flags": [],
            "advice": "AI 分析結果無法解析，請參考規則分析結果。",
        }

    return result
