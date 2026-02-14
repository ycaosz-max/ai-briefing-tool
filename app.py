import streamlit as st
from openai import OpenAI
import os
import tempfile
import pyperclip

# ========== 页面设置 ==========
st.set_page_config(
    page_title="AI语音简报助手", 
    page_icon="🎙️",
    initial_sidebar_state="auto"
)

# ========== iOS 暗黑/明亮模式自动切换样式 ==========
st.markdown("""
<style>
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f0f2f6;
    --bg-card: #ffffff;
    --text-primary: #1f1f1f;
    --text-secondary: #666666;
    --border-color: #e0e0e0;
    --accent-color: #ff4b4b;
    --accent-hover: #ff3333;
    --input-bg: #ffffff;
    --input-text: #1f1f1f;
    --button-text: #ffffff;
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg-primary: #000000;
        --bg-secondary: #1c1c1e;
        --bg-card: #2c2c2e;
        --text-primary: #ffffff;
        --text-secondary: #8e8e93;
        --border-color: #38383a;
        --accent-color: #0a84ff;
        --accent-hover: #409cff;
        --input-bg: #1c1c1e;
        --input-text: #ffffff;
        --button-text: #ffffff;
    }
    .stApp { background-color: #000000 !important; }
    .stTextInput input, .stTextArea textarea {
        background-color: #1c1c1e !important;
        color: #ffffff !important;
        border-color: #38383a !important;
    }
    .stSelectbox > div > div {
        background-color: #2c2c2e !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] {
        background-color: #1c1c1e !important;
    }
}

* {
    -webkit-tap-highlight-color: transparent;
    -webkit-touch-callout: none;
}

.stApp {
    background-color: var(--bg-primary);
    color: var(--text-primary);
    transition: all 0.3s ease;
}

.big-title {
    font-size: 32px;
    font-weight: bold;
    color: var(--text-primary);
    margin-bottom: 8px;
}

.subtitle {
    font-size: 16px;
    color: var(--text-secondary);
    margin-bottom: 24px;
}

.stTextInput input, .stTextArea textarea {
    -webkit-appearance: none !important;
    -webkit-user-select: text !important;
    user-select: text !important;
    font-size: 16px !important;
    touch-action: manipulation;
    border-radius: 10px;
    background-color: var(--input-bg);
    color: var(--input-text);
    border: 1px solid var(--border-color);
}

.stTextInput input:focus, .stTextArea textarea:focus {
    outline: none !important;
    border-color: var(--accent-color) !important;
    box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.3) !important;
}

.stButton button {
    -webkit-appearance: none;
    touch-action: manipulation;
    border-radius: 10px;
    background-color: var(--accent-color) !important;
    color: var(--button-text) !important;
    border: none !important;
    font-weight: 600;
    transition: all 0.2s ease;
}

.stButton button:hover {
    background-color: var(--accent-hover) !important;
    transform: translateY(-1px);
}

.stAlert {
    background-color: var(--bg-card) !important;
    border-color: var(--border-color) !important;
    color: var(--text-primary) !important;
}

.stSuccess {
    background-color: rgba(48, 209, 88, 0.1) !important;
    border-left-color: #30d158 !important;
}

.stInfo {
    background-color: rgba(10, 132, 255, 0.1) !important;
    border-left-color: var(--accent-color) !important;
}

[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
}

/* 下载按钮样式 - 更醒目 */
.download-section {
    margin-top: 20px;
    padding: 20px;
    background: var(--bg-secondary);
    border-radius: 12px;
    border: 2px solid var(--accent-color);
}

.download-title {
    font-size: 16px;
    font-weight: bold;
    color: var(--text-primary);
    margin-bottom: 15px;
    text-align: center;
}

/* 按钮组 */
.action-buttons {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
}

.action-buttons .stButton {
    flex: 1;
    min-width: 120px;
}

/* iOS 提示 */
.ios-hint {
    margin-top: 15px;
    padding: 12px;
    background: rgba(255, 159, 10, 0.1);
    border-left: 3px solid #ff9f0a;
    border-radius: 8px;
    font-size: 13px;
    color: var(--text-secondary);
    line-height: 1.5;
}

@media (max-width: 768px) {
    .big-title { font-size: 26px !important; }
    .subtitle { font-size: 14px !important; }
    .main .block-container { padding: 1rem; }
    .stApp { padding-bottom: env(safe-area-inset-bottom); }
    .action-buttons {
        flex-direction: column;
    }
}

* {
    transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}
</style>

<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
""", unsafe_allow_html=True)

# ========== 标题 ==========
st.markdown('<p class="big-title">🎙️ AI语音简报助手</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">语音直接转文字，自动生成简报</p>', unsafe_allow_html=True)

# ========== API 密钥管理 ==========
api_key = st.session_state.get("api_key", "")

if not api_key:
    st.warning("⚠️ 首次使用需要输入 API 密钥")
    
    with st.expander("🔑 点击此处输入 API 密钥", expanded=True):
        st.markdown("""
        **获取步骤：**
        1. 访问 [硅基流动](https://cloud.siliconflow.cn/i/nZqCjymq)
        2. 注册完成实名认证
        3. 创建您的API密钥
        4. 复制到下方输入框
        """)
        
        api_input = st.text_input(
            "API 密钥",
            value="",
            type="password",
            placeholder="sk-xxxxxxxxxxxxxxxx",
            key="api_key_input",
            help="密钥以 sk- 开头"
        )
        
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("✅ 确认并保存", type="primary", key="save_api_key"):
                if api_input and api_input.startswith("sk-"):
                    st.session_state.api_key = api_input
                    st.success("✅ API 密钥已保存！")
                    st.rerun()
                else:
                    st.error("❌ 请输入正确的 API 密钥（以 sk- 开头）")
    
    st.stop()

# ========== 侧边栏 ==========
with st.sidebar:
    st.header("⚙️ 设置")
    st.success("✅ API 已配置")
    if st.button("🔄 更换 API 密钥"):
        del st.session_state.api_key
        st.rerun()
    st.divider()
    st.caption("💡 AI简报_分享版 v2.2.2")

# ========== 语音转文字函数（修复 text 问题） ==========
def transcribe_audio(audio_bytes, api_key):
    tmp_path = None
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        with open(tmp_path, "rb") as audio:
            # 使用 text 格式直接获取纯文本
            transcription = client.audio.transcriptions.create(
                model="FunAudioLLM/SenseVoiceSmall",
                file=audio,
                response_format="text"
            )
            
            # 处理返回结果
            result_text = ""
            
            # 如果是对象，获取 text 属性
            if hasattr(transcription, 'text'):
                result_text = transcription.text
            elif isinstance(transcription, str):
                result_text = transcription
            else:
                result_text = str(transcription)
            
            # 清理：去除 text= 前缀和引号
            result_text = result_text.strip()
            if result_text.startswith('text='):
                result_text = result_text[5:]
            result_text = result_text.strip("'\"")
