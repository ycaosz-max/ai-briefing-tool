# AI简报小助手 - iOS 原生风格版 v3.0
# 设计规范：iOS Human Interface Guidelines
# 特点：圆角、毛玻璃、统一配色、SF字体风格

import streamlit as st
from openai import OpenAI
import os
import tempfile

# ========== 页面设置 ==========
st.set_page_config(
    page_title="AI语音简报",
    page_icon="🎙️",
    initial_sidebar_state="collapsed",  # iOS风格：简洁，默认收起
    layout="centered"  # iOS风格：居中窄布局，更适合手机
)

# ========== iOS 原生风格 CSS ==========
st.markdown("""
<style>
/* iOS 基础变量 */
:root {
    --ios-bg: #F2F2F7;           /* iOS系统灰 */
    --ios-card: #FFFFFF;          /* 卡片白 */
    --ios-blue: #007AFF;          /* iOS蓝 */
    --ios-green: #34C759;         /* iOS绿 */
    --ios-red: #FF3B30;           /* iOS红 */
    --ios-orange: #FF9500;        /* iOS橙 */
    --ios-gray: #8E8E93;          /* iOS灰 */
    --ios-light-gray: #E5E5EA;    /* iOS浅灰 */
    --ios-text: #000000;          /* 主文字 */
    --ios-text-secondary: #3C3C43; /* 次要文字 60%透明度 */
    --ios-radius: 10px;           /* iOS标准圆角 */
    --ios-radius-lg: 16px;        /* iOS大圆角 */
    --ios-shadow: 0 2px 8px rgba(0,0,0,0.08); /* iOS阴影 */
}

/* 全局 iOS 风格 */
* {
    -webkit-tap-highlight-color: transparent;
    -webkit-touch-callout: none;
    font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Segoe UI', Roboto, sans-serif !important;
}

.stApp {
    background-color: var(--ios-bg) !important;
}

/* iOS 导航栏风格标题 */
.ios-nav {
    background: rgba(255,255,255,0.85);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-bottom: 0.5px solid var(--ios-light-gray);
    padding: 12px 16px;
    margin: -1rem -1rem 1rem -1rem;
    text-align: center;
    position: sticky;
    top: 0;
    z-index: 100;
}

.ios-nav-title {
    font-size: 17px;
    font-weight: 600;
    color: var(--ios-text);
    letter-spacing: -0.01em;
}

/* iOS 卡片 */
.ios-card {
    background: var(--ios-card);
    border-radius: var(--ios-radius-lg);
    padding: 16px;
    margin-bottom: 12px;
    box-shadow: var(--ios-shadow);
    border: none;
}

.ios-card h3 {
    font-size: 20px;
    font-weight: 600;
    margin: 0 0 12px 0;
    color: var(--ios-text);
}

/* iOS 分组标题 */
.ios-section-title {
    font-size: 13px;
    font-weight: 400;
    color: var(--ios-gray);
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 20px 16px 8px 16px;
}

/* iOS 按钮 - 主要 */
.ios-button-primary {
    background: var(--ios-blue) !important;
    color: white !important;
    border-radius: var(--ios-radius) !important;
    padding: 12px 24px !important;
    font-size: 17px !important;
    font-weight: 500 !important;
    border: none !important;
    width: 100% !important;
    height: 50px !important;
    transition: all 0.2s ease;
}

.ios-button-primary:active {
    opacity: 0.8;
    transform: scale(0.98);
}

/* iOS 按钮 - 次要 */
.ios-button-secondary {
    background: var(--ios-light-gray) !important;
    color: var(--ios-blue) !important;
    border-radius: var(--ios-radius) !important;
    padding: 12px 24px !important;
    font-size: 17px !important;
    font-weight: 500 !important;
    border: none !important;
    width: 100% !important;
    height: 50px !important;
}

/* iOS 输入框 */
.stTextInput input, .stTextArea textarea {
    background: var(--ios-card) !important;
    border: none !important;
    border-radius: var(--ios-radius) !important;
    padding: 12px 16px !important;
    font-size: 17px !important;
    color: var(--ios-text) !important;
    box-shadow: inset 0 0 0 0.5px var(--ios-light-gray) !important;
    -webkit-appearance: none !important;
    min-height: 50px !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
    box-shadow: inset 0 0 0 2px var(--ios-blue) !important;
}

/* iOS 选择器 */
.stSelectbox > div > div {
    background: var(--ios-card) !important;
    border-radius: var(--ios-radius) !important;
    border: none !important;
    padding: 4px !important;
    font-size: 17px !important;
}

/* iOS 文件上传 */
.stFileUploader > div > div {
    background: var(--ios-card) !important;
    border: 2px dashed var(--ios-light-gray) !important;
    border-radius: var(--ios-radius-lg) !important;
    padding: 30px !important;
}

/* iOS 标签页 */
.ios-segment {
    display: flex;
    background: var(--ios-light-gray);
    border-radius: var(--ios-radius);
    padding: 2px;
    margin-bottom: 16px;
}

.ios-segment-item {
    flex: 1;
    text-align: center;
    padding: 8px;
    border-radius: 8px;
    font-size: 15px;
    font-weight: 500;
    color: var(--ios-text);
}

.ios-segment-item.active {
    background: var(--ios-card);
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
}

/* iOS 列表项 */
.ios-list-item {
    background: var(--ios-card);
    padding: 12px 16px;
    border-bottom: 0.5px solid var(--ios-light-gray);
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.ios-list-item:first-child {
    border-radius: var(--ios-radius-lg) var(--ios-radius-lg) 0 0;
}

.ios-list-item:last-child {
    border-radius: 0 0 var(--ios-radius-lg) var(--ios-radius-lg);
    border-bottom: none;
}

/* iOS 开关 */
.ios-toggle {
    width: 51px;
    height: 31px;
    background: var(--ios-light-gray);
    border-radius: 16px;
    position: relative;
    transition: background 0.3s;
}

.ios-toggle.active {
    background: var(--ios-green);
}

/* iOS 提示 */
.ios-alert {
    background: rgba(255,255,255,0.95);
    backdrop-filter: blur(20px);
    border-radius: var(--ios-radius-lg);
    padding: 16px;
    margin: 12px 0;
    text-align: center;
}

/* 移动端优化 */
@media (max-width: 768px) {
    .main .block-container {
        padding: 0 12px 20px 12px !important;
        max-width: 100% !important;
    }
    
    .ios-card {
        border-radius: var(--ios-radius);
        margin-bottom: 8px;
    }
}

/* 隐藏 Streamlit 默认元素 */
header[data-testid="stHeader"] { display: none; }
.stDeployButton { display: none; }

/* iOS 录音按钮特殊样式 */
.ios-record-btn {
    width: 72px !important;
    height: 72px !important;
    border-radius: 50% !important;
    background: var(--ios-red) !important;
    border: 4px solid rgba(255,255,255,0.3) !important;
    box-shadow: 0 4px 15px rgba(255,59,48,0.4) !important;
    margin: 20px auto !important;
    display: block !important;
    transition: transform 0.2s !important;
}

.ios-record-btn:active {
    transform: scale(0.95);
}

/* iOS 成功/错误提示 */
.stAlert {
    border-radius: var(--ios-radius) !important;
    border: none !important;
    background: rgba(52,199,89,0.1) !important; /* 成功绿 */
}

.stAlert[data-baseweb="notification"] {
    background: rgba(255,59,48,0.1) !important; /* 错误红 */
}

/* iOS 分割线 */
hr {
    border: none !important;
    height: 0.5px !important;
    background: var(--ios-light-gray) !important;
    margin: 16px 0 !important;
}

/* iOS 底部安全区 */
.ios-safe-bottom {
    height: 34px;
}
</style>
""", unsafe_allow_html=True)

# ========== iOS 风格导航栏 ==========
st.markdown("""
<div class="ios-nav">
    <div class="ios-nav-title">AI语音简报</div>
</div>
""", unsafe_allow_html=True)

# ========== API 密钥管理 ==========
api_key = st.session_state.get("api_key", "")

if not api_key:
    # iOS 风格登录页
    st.markdown("""
    <div class="ios-card" style="text-align: center; padding: 32px 24px; margin-top: 20px;">
        <div style="font-size: 64px; margin-bottom: 16px;">🎙️</div>
        <h2 style="font-size: 22px; font-weight: 600; margin-bottom: 8px; color: var(--ios-text);">
            欢迎使用
        </h2>
        <p style="font-size: 17px; color: var(--ios-gray); margin-bottom: 24px;">
            语音转文字，智能生成简报
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # iOS 分组标题风格
    st.markdown('<div class="ios-section-title">API 密钥设置</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="ios-card">', unsafe_allow_html=True)
        
        st.markdown("""
        <p style="font-size: 15px; color: var(--ios-text-secondary); margin-bottom: 16px; line-height: 1.5;">
            首次使用需要配置 API 密钥。请前往硅基流动官网获取免费密钥。
        </p>
        """, unsafe_allow_html=True)
        
        # iOS 风格输入框
        api_input = st.text_input(
            "",
            value="",
            type="password",
            placeholder="sk-xxxxxxxxxxxxxxxx",
            key="api_key_input",
            label_visibility="collapsed"
        )
        
        # iOS 风格主要按钮
        if st.button("继续", type="primary", use_container_width=True, key="save_api_key"):
            if api_input and api_input.startswith("sk-"):
                st.session_state.api_key = api_input
                st.success("配置成功")
                st.rerun()
            else:
                st.error("密钥格式错误，应以 sk- 开头")
        
        # iOS 风格链接按钮
        st.markdown("""
        <a href="https://cloud.siliconflow.cn/i/nZqCjymq" target="_blank" 
           style="display: block; text-align: center; color: var(--ios-blue); 
                  font-size: 17px; text-decoration: none; margin-top: 16px; padding: 12px;">
            获取免费 API 密钥 →
        </a>
        """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.stop()

# ========== 侧边栏（iOS 设置风格）=========
with st.sidebar:
    st.markdown('<div class="ios-section-title">设置</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="ios-card">', unsafe_allow_html=True)
        st.markdown("""
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span style="font-size: 17px; color: var(--ios-text);">API 状态</span>
            <span style="color: var(--ios-green); font-size: 15px;">已配置</span>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        if st.button("更换 API 密钥", use_container_width=True):
            del st.session_state.api_key
            st.rerun()
    
    st.markdown('<div class="ios-safe-bottom"></div>', unsafe_allow_html=True)

# ========== 语音转文字函数 ==========
def transcribe_audio(audio_bytes, api_key):
    try:
        client = OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        with open(tmp_path, "rb") as audio:
            transcription = client.audio.transcriptions.create(
                model="FunAudioLLM/SenseVoiceSmall",
                file=audio,
                response_format="text"
            )
        
        os.unlink(tmp_path)
        return {"success": True, "text": transcription}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========== 主界面（iOS 标签页风格）=========
st.markdown('<div class="ios-section-title">语音输入</div>', unsafe_allow_html=True)

# iOS 分段控制器
tab_col1, tab_col2 = st.columns(2)
with tab_col1:
    record_tab = st.button("🎙️ 录音", use_container_width=True, type="primary" if st.session_state.get("input_tab", "record") == "record" else "secondary")
    if record_tab:
        st.session_state.input_tab = "record"

with tab_col2:
    upload_tab = st.button("📁 上传", use_container_width=True, type="primary" if st.session_state.get("input_tab", "record") == "upload" else "secondary")
    if upload_tab:
        st.session_state.input_tab = "upload"

input_tab = st.session_state.get("input_tab", "record")

# 录音标签页
if input_tab == "record":
    with st.container():
        st.markdown('<div class="ios-card" style="text-align: center; padding: 24px;">', unsafe_allow_html=True)
        
        st.markdown("""
        <p style="font-size: 15px; color: var(--ios-gray); margin-bottom: 20px;">
            点击开始录音，说话后自动转写
        </p>
        """, unsafe_allow_html=True)
        
        try:
            from streamlit_mic_recorder import mic_recorder
            
            audio = mic_recorder(
                start_prompt="",
                stop_prompt="",
                just_once=True,
                key="mic_ios"
            )
            
            if audio and audio.get("bytes"):
                with st.spinner("识别中..."):
                    result = transcribe_audio(audio["bytes"], api_key)
                    
                    if result["success"]:
                        st.session_state.transcribed_text = result["text"]
                        st.success(f"识别完成，{len(result['text'])} 字")
                        st.rerun()
                    else:
                        st.error("识别失败")
                        
        except ImportError:
            st.error("录音组件未加载")
        
        st.markdown('</div>', unsafe_allow_html=True)

# 上传标签页
else:
    with st.container():
        st.markdown('<div class="ios-card">', unsafe_allow_html=True)
        
        st.markdown("""
        <p style="font-size: 15px; color: var(--ios-gray); margin-bottom: 16px;">
            支持 mp3、wav、m4a 格式
        </p>
        """, unsafe_allow_html=True)
        
        audio_file = st.file_uploader("", type=['mp3', 'wav', 'm4a', 'webm'], label_visibility="collapsed")
        
        if audio_file:
            st.audio(audio_file, format=f'audio/{audio_file.type.split("/")[1]}')
            
            if st.button("开始识别", type="primary", use_container_width=True):
                with st.spinner("识别中..."):
                    result = transcribe_audio(audio_file.getvalue(), api_key)
                    
                    if result["success"]:
                        st.session_state.transcribed_text = result["text"]
                        st.success(f"识别完成，{len(result['text'])} 字")
                        st.rerun()
                    else:
                        st.error("识别失败")
        
        st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="ios-section-title">编辑与生成</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="ios-card">', unsafe_allow_html=True)
    
    # iOS 风格选择器
    briefing_type = st.segmented_control(
        "简报类型",
        options=["会议纪要", "工作日报", "学习笔记", "新闻摘要"],
        default="会议纪要",
        key="briefing_type_ios"
    )
    
    # 如果没有 segmented_control，使用普通 selectbox
    if 'briefing_type_ios' not in st.session_state:
        briefing_type = st.selectbox(
            "简报类型",
            ["会议纪要", "工作日报", "学习笔记", "新闻摘要"],
            key="briefing_type"
        )
    
    # 文本编辑区
    content = st.text_area(
        "",
        value=st.session_state.get("transcribed_text", ""),
        height=200,
        placeholder="语音内容将显示在这里，可直接编辑...",
        label_visibility="collapsed"
    )
    
    if content != st.session_state.get("transcribed_text", ""):
        st.session_state.transcribed_text = content
    
    # 特殊要求（iOS 风格折叠）
    with st.expander("高级选项"):
        custom_req = st.text_input("特殊要求", placeholder="例如：突出重点、精简内容")
    
    # 生成按钮
    col_gen, col_clear = st.columns([3, 1])
    with col_gen:
        if st.button("生成简报", type="primary", use_container_width=True):
            if not content.strip():
                st.error("请输入内容")
            else:
                with st.spinner("生成中..."):
                    try:
                        client = OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")
                        
                        prompts = {
                            "会议纪要": "整理成会议纪要：1主题 2讨论 3决议 4待办",
                            "工作日报": "整理成工作日报：1完成 2问题 3计划",
                            "学习笔记": "整理成学习笔记：1概念 2重点 3思考",
                            "新闻摘要": "整理成新闻摘要：1事件 2数据 3影响"
                        }
                        
                        prompt = prompts.get(briefing_type, prompts["会议纪要"])
                        if custom_req:
                            prompt += f"。要求：{custom_req}"
                        
                        response = client.chat.completions.create(
                            model="deepseek-ai/DeepSeek-V3",
                            messages=[
                                {"role": "system", "content": prompt},
                                {"role": "user", "content": content}
                            ],
                            temperature=0.7,
                            max_tokens=2000
                        )
                        
                        st.session_state.generated_result = response.choices[0].message.content
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"生成失败：{str(e)}")
    
    with col_clear:
        if st.button("清空", use_container_width=True):
            st.session_state.transcribed_text = ""
            if "generated_result" in st.session_state:
                del st.session_state.generated_result
            st.rerun()
    
    st.markdown('</div>', unsafe_allow_html=True)

# 结果显示
if "generated_result" in st.session_state:
    st.markdown('<div class="ios-section-title">生成结果</div>', unsafe_allow_html=True)
    
    with st.container():
        st.markdown('<div class="ios-card">', unsafe_allow_html=True)
        st.markdown(st.session_state.generated_result)
        
        st.download_button(
            "下载简报",
            st.session_state.generated_result,
            file_name=f"简报_{briefing_type}.txt",
            use_container_width=True
        )
        
        st.markdown('</div>', unsafe_allow_html=True)

# iOS 底部安全区
st.markdown('<div class="ios-safe-bottom"></div>', unsafe_allow_html=True)
