"""AI 防詐騙助手 — Streamlit 網頁版（支援截圖）"""
import streamlit as st
import sys
import os
from PIL import Image

sys.path.insert(0, os.path.dirname(__file__))

from modules.analyzer import analyze_message, AnalysisResult
from data.scam_patterns import SCAM_TYPES, OFFICIAL_CONTACTS

st.set_page_config(
    page_title="AI 防詐騙助手",
    layout="wide",
)

# ── CSS ──
st.markdown("""
<style>
.risk-extreme { background: #D32F2F; color: white; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; }
.risk-high { background: #F57C00; color: white; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; }
.risk-medium { background: #FFA000; color: white; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; }
.risk-low { background: #388E3C; color: white; padding: 20px; border-radius: 10px; text-align: center; font-size: 24px; }
.keyword-tag { display: inline-block; background: #FFE0E0; color: #C62828; padding: 4px 12px; border-radius: 20px; margin: 4px; font-size: 14px; }
.flag-tag { display: inline-block; background: #FFF3E0; color: #E65100; padding: 4px 12px; border-radius: 20px; margin: 4px; font-size: 14px; }
.advice-box { background: #E3F2FD; padding: 20px; border-radius: 10px; border-left: 5px solid #1976D2; margin: 10px 0; }
.info-box { background: #F3E5F5; padding: 15px; border-radius: 10px; margin: 5px 0; }
</style>
""", unsafe_allow_html=True)

# ── Header ──
st.title("AI 防詐騙助手")
st.markdown("貼上可疑訊息或上傳截圖，AI 幫你判斷是不是詐騙")
st.markdown("---")

# ── 主要區域 ──
col_input, col_result = st.columns([1, 1])

with col_input:
    # 輸入模式切換
    input_mode = st.radio("輸入方式", ["貼上文字", "上傳截圖"], horizontal=True)

    message = ""
    analyze_btn = False

    if input_mode == "貼上文字":
        message = st.text_area(
            "把你收到的可疑訊息貼在這裡：",
            height=250,
            placeholder="例如：\n恭喜你中獎了！請點擊連結領取...\n或\n我是某某老師，跟著我的投資群組保證獲利...",
        )
        analyze_btn = st.button("分析這段訊息", type="primary", use_container_width=True)

    else:  # 上傳截圖
        uploaded = st.file_uploader(
            "上傳 LINE / 簡訊 / Email 截圖",
            type=["png", "jpg", "jpeg", "webp"],
        )
        if uploaded:
            image = Image.open(uploaded)
            st.image(image, caption="你上傳的截圖", use_container_width=True)

        analyze_btn = st.button("辨識並分析截圖", type="primary", use_container_width=True)

        if analyze_btn and uploaded:
            with st.spinner("正在辨識截圖文字（第一次會比較慢，需要載入模型）..."):
                from modules.ocr import extract_text_from_image
                image = Image.open(uploaded)
                message = extract_text_from_image(image)
                if message.strip():
                    st.success("辨識到的文字：")
                    st.code(message, language=None)
                else:
                    st.error("無法從截圖中辨識出文字，請試試貼上文字模式")

    # 快速測試範例
    st.markdown("---")
    st.markdown("**快速測試（點擊試試看）：**")

    examples = {
        "假投資": "恭喜你被選入VIP投資群組！老師帶單保證獲利，已有上百位學員月入10萬以上。限時名額只剩3位，趕快加我LINE：invest_master888，先入金5000就能開始賺錢！",
        "假冒客服": "【重要通知】您的信用卡帳戶異常，已被暫時凍結。請立即點擊連結 https://bank-verify.cc/tw 進行身份驗證，否則將於24小時內永久停用。客服專線：02-8888-7777",
        "感情詐騙": "親愛的，我在美國當軍醫，下個月就退役了，好想飛去台灣見你。但是我的包裹卡在海關，需要繳一筆手續費才能領出來，你能先幫我代墊嗎？我到台灣馬上還你，你是我這輩子最重要的人。",
        "求職詐騙": "【高薪急徵】在家工作日領3000！不需經驗，只要有手機就能做。工作內容：幫商家刷單衝評價，每單佣金50-200元。先加LINE：job_easy999 了解詳情。需提供銀行帳戶以便發薪。",
        "正常訊息": "嗨，明天下午三點在學校門口集合，記得帶課本。晚上要不要一起吃飯？",
    }

    for label, text in examples.items():
        if st.button(f"測試：{label}", use_container_width=True):
            st.session_state["test_message"] = text
            st.rerun()

# 處理測試訊息
if "test_message" in st.session_state:
    message = st.session_state.pop("test_message")
    analyze_btn = True

with col_result:
    st.subheader("分析結果")

    if analyze_btn and message.strip():
        result = analyze_message(message)

        # 風險等級顯示
        risk_class = {
            "極高": "risk-extreme",
            "高": "risk-high",
            "中": "risk-medium",
            "低": "risk-low",
        }
        css_class = risk_class.get(result.risk_level, "risk-low")

        st.markdown(
            f'<div class="{css_class}">詐騙風險：{result.risk_level} ({result.risk_score:.0f}%)</div>',
            unsafe_allow_html=True,
        )
        st.markdown("")

        # 風險條
        st.progress(result.risk_score / 100)

        # 詐騙類型
        if result.scam_type_name != "未知類型":
            st.markdown(f"### 可能的詐騙類型：{result.scam_type_name}")
            st.markdown(f"*{result.description}*")
        else:
            st.markdown("### 看起來風險較低")
            st.markdown("*但仍請保持警覺，詐騙手法持續翻新*")

        st.markdown("---")

        # 偵測到的關鍵字
        if result.matched_keywords:
            st.markdown("**偵測到的可疑關鍵字：**")
            kw_html = " ".join([f'<span class="keyword-tag">{kw}</span>' for kw in result.matched_keywords[:10]])
            st.markdown(kw_html, unsafe_allow_html=True)
            st.markdown("")

        # 警告訊號
        if result.universal_flags:
            st.markdown("**警告訊號：**")
            flag_html = " ".join([f'<span class="flag-tag">[!] {f}</span>' for f in result.universal_flags])
            st.markdown(flag_html, unsafe_allow_html=True)
            st.markdown("")

        # 紅旗說明
        if result.red_flags:
            st.markdown("**你應該知道的事：**")
            for rf in result.red_flags:
                st.warning(rf)

        # 建議
        st.markdown(
            f'<div class="advice-box"><strong>建議：</strong><br>{result.advice}</div>',
            unsafe_allow_html=True,
        )

        # ── AI 語意分析 ──
        if groq_key:
            st.markdown("---")
            st.markdown("### AI 語意分析")
            with st.spinner("AI 正在深度分析..."):
                try:
                    from modules.ai_analyzer import ai_analyze
                    ai_result = ai_analyze(message, groq_key)

                    if ai_result.get("is_scam"):
                        st.error(f"**AI 判斷：這是詐騙（信心 {ai_result.get('confidence', '?')}%）**")
                    elif ai_result.get("is_scam") is False:
                        st.success(f"**AI 判斷：這不是詐騙（信心 {ai_result.get('confidence', '?')}%）**")
                    else:
                        st.warning("**AI 無法確定**")

                    st.markdown(f"**類型：** {ai_result.get('scam_type', '未知')}")
                    st.markdown(f"**分析：** {ai_result.get('explanation', '')}")

                    ai_flags = ai_result.get("red_flags", [])
                    if ai_flags:
                        st.markdown("**AI 發現的可疑點：**")
                        for flag in ai_flags:
                            st.markdown(f"- {flag}")

                    ai_advice = ai_result.get("advice", "")
                    if ai_advice:
                        st.markdown(
                            f'<div class="advice-box"><strong>AI 建議：</strong><br>{ai_advice}</div>',
                            unsafe_allow_html=True,
                        )
                except Exception as e:
                    st.error(f"AI 分析失敗：{e}")

        # 緊急聯絡
        st.markdown("")
        st.markdown("**緊急聯絡方式：**")
        contact_cols = st.columns(len(OFFICIAL_CONTACTS))
        for i, (name, number) in enumerate(OFFICIAL_CONTACTS.items()):
            with contact_cols[i]:
                st.markdown(
                    f'<div class="info-box"><strong>{name}</strong><br>{number}</div>',
                    unsafe_allow_html=True,
                )

    elif analyze_btn:
        st.warning("請先貼上訊息或上傳截圖")
    else:
        st.info("在左側貼上可疑訊息或上傳截圖，點「分析」即可看到結果。\n\n也可以點下方的快速測試範例試試看。")

# ── Footer ──
st.markdown("---")
st.caption("此工具僅供參考，不能取代專業判斷。如遇疑似詐騙請撥 165 反詐騙專線。")

# ── Sidebar ──
with st.sidebar:
    st.title("設定")
    groq_key = st.text_input("Groq API Key（免費申請）", type="password", help="到 https://console.groq.com 免費申請")
    if groq_key:
        st.success("AI 分析已啟用")
    else:
        st.info("輸入 Groq API Key 即可啟用 AI 語意分析（免費）")

    st.markdown("---")
    st.title("詐騙知識庫")
    st.markdown("---")

    for type_id, info in SCAM_TYPES.items():
        with st.expander(info["name"]):
            st.markdown(f"**{info['description']}**")
            st.markdown("")
            st.markdown("常見手法：")
            for rf in info["red_flags"]:
                st.markdown(f"- {rf}")
            st.markdown("")
            st.markdown(f"**建議：** {info['advice']}")

    st.markdown("---")
    st.markdown("**緊急電話**")
    for name, number in OFFICIAL_CONTACTS.items():
        st.markdown(f"- {name}：**{number}**")
