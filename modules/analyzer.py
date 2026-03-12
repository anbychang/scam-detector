"""P1：詐騙分析引擎"""
import re
from dataclasses import dataclass, field
from data.scam_patterns import SCAM_TYPES, UNIVERSAL_RED_FLAGS, OFFICIAL_CONTACTS


@dataclass
class AnalysisResult:
    risk_score: float  # 0~100
    risk_level: str  # 低/中/高/極高
    scam_type: str  # 最可能的詐騙類型
    scam_type_name: str
    matched_keywords: list = field(default_factory=list)
    red_flags: list = field(default_factory=list)
    universal_flags: list = field(default_factory=list)
    advice: str = ""
    description: str = ""


def analyze_message(text: str) -> AnalysisResult:
    """分析一段文字是否為詐騙"""
    text_lower = text.lower()

    # === 1. 比對各詐騙類型 ===
    type_scores = {}
    type_matches = {}

    for type_id, info in SCAM_TYPES.items():
        matches = []
        for kw in info["keywords"]:
            if kw.lower() in text_lower:
                matches.append(kw)
        score = len(matches)
        type_scores[type_id] = score
        type_matches[type_id] = matches

    # === 2. 比對通用紅旗 ===
    universal_hits = []
    universal_score = 0

    for flag in UNIVERSAL_RED_FLAGS:
        for kw in flag["keywords"]:
            if kw in text_lower:
                universal_hits.append(flag["pattern"])
                universal_score += flag["weight"]
                break  # 每個 pattern 只算一次

    # === 3. 文本特徵分析 ===
    feature_score = 0
    feature_flags = []

    # 有連結
    urls = re.findall(r'https?://\S+|bit\.ly/\S+|reurl\.cc/\S+', text)
    if urls:
        feature_score += 2
        feature_flags.append("包含連結")

    # 有電話號碼
    phones = re.findall(r'09\d{8}|\+\d{10,}', text)
    if phones:
        feature_score += 1

    # 有 LINE ID
    if re.search(r'line\s*[：:]\s*\S+|加.*line|line.*id', text_lower):
        feature_score += 2
        feature_flags.append("要求加 LINE")

    # 有金額
    money = re.findall(r'\d+[萬千百億]|\$\d+|NT\$?\d+|\d+元', text)
    if money:
        feature_score += 1

    # 全形驚嘆號很多（詐騙愛用）
    exclamation = text.count('！') + text.count('!')
    if exclamation >= 3:
        feature_score += 1
        feature_flags.append("大量驚嘆號")

    # 表情符號很多
    emoji_count = len(re.findall(r'[\U0001F600-\U0001F9FF]', text))
    if emoji_count >= 5:
        feature_score += 1

    # === 4. 計算總分 ===
    best_type = max(type_scores, key=type_scores.get)
    best_type_score = type_scores[best_type]

    # 加權總分
    raw_score = (best_type_score * 8) + (universal_score * 10) + (feature_score * 5)

    # 正規化到 0~100
    risk_score = min(100, raw_score)

    # 風險等級
    if risk_score >= 75:
        risk_level = "極高"
    elif risk_score >= 50:
        risk_level = "高"
    elif risk_score >= 25:
        risk_level = "中"
    else:
        risk_level = "低"

    # === 5. 組合結果 ===
    scam_info = SCAM_TYPES[best_type]

    # 紅旗列表
    red_flags = []
    if best_type_score > 0:
        red_flags.extend(scam_info["red_flags"][:3])

    result = AnalysisResult(
        risk_score=risk_score,
        risk_level=risk_level,
        scam_type=best_type,
        scam_type_name=scam_info["name"] if best_type_score > 0 else "未知類型",
        matched_keywords=type_matches[best_type] + feature_flags,
        red_flags=red_flags,
        universal_flags=universal_hits,
        advice=scam_info["advice"] if best_type_score > 0 else "此訊息看起來風險較低，但仍請保持警覺。如有疑慮請撥 165 反詐騙專線。",
        description=scam_info["description"] if best_type_score > 0 else "",
    )

    return result


def format_result(result: AnalysisResult) -> str:
    """格式化分析結果為文字"""
    # 風險條
    bar_len = 20
    filled = int(result.risk_score / 100 * bar_len)
    bar = "X" * filled + "-" * (bar_len - filled)

    lines = []
    lines.append("=" * 50)
    lines.append("  詐騙風險分析結果")
    lines.append("=" * 50)
    lines.append("")
    lines.append(f"  風險分數：{result.risk_score:.0f}/100")
    lines.append(f"  風險等級：{result.risk_level}")
    lines.append(f"  [{bar}]")
    lines.append("")

    if result.scam_type_name != "未知類型":
        lines.append(f"  可能的詐騙類型：{result.scam_type_name}")
        lines.append(f"  說明：{result.description}")
        lines.append("")

    if result.matched_keywords:
        lines.append("  偵測到的關鍵字：")
        for kw in result.matched_keywords[:8]:
            lines.append(f"    - {kw}")
        lines.append("")

    if result.universal_flags:
        lines.append("  警告訊號：")
        for flag in result.universal_flags:
            lines.append(f"    [!] {flag}")
        lines.append("")

    if result.red_flags:
        lines.append("  你應該知道的事：")
        for rf in result.red_flags:
            lines.append(f"    > {rf}")
        lines.append("")

    lines.append("  建議：")
    lines.append(f"    {result.advice}")
    lines.append("")
    lines.append(f"  反詐騙專線：165")
    lines.append(f"  報警：110")
    lines.append("=" * 50)

    return "\n".join(lines)
