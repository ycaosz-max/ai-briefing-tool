import streamlit as st
from openai import OpenAI
import os
import tempfile
import json

# ========== 页面设置 ==========
st.set_page_config(
    page_title="AI语音简报助手", 
    page_icon="🎙️",
    initial_sidebar_state="auto"
)

# ========== iOS 暗黑/明亮模式自动切换样式 ==========
st.markdown("""
<style>
/* ========== 基础变量定义 ========== */
:root {
    /* 明亮模式默认 */
    --bg-primary: #ffffff;
    --bg-secondary: #f0f2f6;
    --bg-card: #ffffff;
    --text-primary: #1f1f1f;
    --text-secondary: #666666;
    --border-color: #e0e0e0;
    --accent-color: #ff4b4b;
    --accent-hover: #ff3333;
    --shadow: rgba(0, 0, 0, 0.1);
    --input-bg: #ffffff;
    --input-text: #1f1f1f;
    --button-text: #ffffff;
}

/* ========== iOS 暗黑模式检测 ========== */
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
        --shadow: rgba(0, 0, 0, 0.5);
        --input-bg: #1c1c1e;
        --input-text: #ffffff;
        --button-text: #ffffff;
    }
    
    /* Streamlit 暗黑模式覆盖 */
    .stApp {
        background-color: var(--bg-primary) !important;
    }
    
    .stTextInput input, .stTextArea textarea {
        background-color: var(--input-bg) !important;
        color: var(--input-text) !important;
        border-color: var(--border-color) !important;
    }
    
    .stSelectbox > div > div {
        background-color: var(--bg-card) !important;
        color: var(--text-primary) !important;
    }
    
    .stExpander {
        background-color: var(--bg-card) !important;
        border-color: var(--border-color) !important;
    }
    
    .stMarkdown {
        color: var(--text-primary) !important;
    }
    
    /* 侧边栏暗黑模式 */
    .css-1d391kg, .css-1lcbmhc {
        background-color: var(--bg-secondary) !important;
    }
}

/* ========== iOS 基础修复 ========== */
* {
    -webkit-tap-highlight-color: transparent;
    -webkit-touch-callout: none;
}

/* ========== 全局样式应用 ========== */
.stApp {
    background-color: var(--bg-primary);
    color: var(--text-primary);
    transition: background-color 0.3s ease, color 0.3s ease;
}

/* 标题样式 */
.big-title {
    font-size: 32px;
    font-weight: bold;
    color: var(--text-primary);
    margin-bottom: 8px;
    transition: color 0.3s ease;
}

.subtitle {
    font-size: 16px;
    color: var(--text-secondary);
    margin-bottom: 24px;
    transition: color 0.3s ease;
}

/* 输入框样式 - 自动适应主题 */
.stTextInput input, .stTextArea textarea {
    -webkit-appearance: none !important;
    -webkit-user-select: text !important;
    user-select: text !important;
    font-size: 16px !important;
    touch-action: manipulation;
    -webkit-border-radius: 10px;
    border-radius: 10px;
    background-color: var(--input-bg);
    color: var(--input-text);
    border: 1px solid var(--border-color);
    transition: all 0.3s ease;
}

/* 输入框焦点样式 */
.stTextInput input:focus, .stTextArea textarea:focus {
    outline: none !important;
    border-color: var(--accent-color) !important;
    box-shadow: 0 0 0 3px rgba(10, 132, 255, 0.3) !important;
}

/* 按钮样式 - 高对比度 */
.stButton button {
    -webkit-appearance: none;
    touch-action: manipulation;
    -webkit-border-radius: 10px;
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

.stButton button:active {
    transform: translateY(0);
}

/* 卡片/容器样式 */
.stExpander {
    background-color: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    overflow: hidden;
    transition: all 0.3s ease;
}

/* 信息框样式 - 暗黑模式适配 */
.stAlert {
    background-color: var(--bg-card) !important;
    border-color: var(--border-color) !important;
    color: var(--text-primary) !important;
}

.stInfo {
    background-color: rgba(10, 132, 255, 0.1) !important;
    border-left-color: var(--accent-color) !important;
}

.stSuccess {
    background-color: rgba(48, 209, 88, 0.1) !important;
    border-left-color: #30d158 !important;
}

.stWarning {
    background-color: rgba(255, 159, 10, 0.1) !important;
    border-left-color: #ff9f0a !important;
}

.stError {
    background-color: rgba(255, 69, 58, 0.1) !important;
    border-left-color: #ff453a !important;
}

/* 文件上传区域 */
.stFileUploader > div > div {
    background-color: var(--bg-secondary) !important;
    border-color: var(--border-color) !important;
    color: var(--text-primary) !important;
}

/* 分割线 */
hr {
    border-color: var(--border-color) !important;
}

/* 下载按钮 */
.stDownloadButton button {
    background-color: var(--bg-card) !important;
    color: var(--accent-color) !important;
    border: 2px solid var(--accent-color) !important;
}

.stDownloadButton button:hover {
    background-color: var(--accent-color) !important;
    color: var(--button-text) !important;
}

/* 侧边栏样式 */
.css-1d391kg, .css-1lcbmhc, [data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
}

/* 选择框样式 */
.stSelectbox > div > div {
    background-color: var(--bg-card);
    border-color: var(--border-color) !important;
    color: var(--text-primary);
    border-radius: 10px;
}

/* 移动端适配 */
@media (max-width: 768px) {
    .big-title { 
        font-size: 26px !important; 
    }
    .subtitle { 
        font-size: 14px !important; 
    }
    .main .block-container { 
        padding: 1rem; 
    }
    
    /* iOS 安全区域适配 */
    .stApp {
        padding-bottom: env(safe-area-inset-bottom);
    }
}

/* 平滑过渡动画 */
* {
    transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}

/* 自定义加载提示样式 */
.processing-hint {
    background: linear-gradient(135deg, var(--accent-color) 0%, var(--accent-hover) 100%);
    color: white;
    padding: 15px 20px;
    border-radius: 12px;
    margin: 10px 0;
    text-align: center;
    font-size: 14px;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
}

.processing-steps {
    background: var(--bg-secondary);
    padding: 15px;
    border-radius: 10px;
    margin-top: 10px;
    font-size: 13px;
    color: var(--text-secondary);
}

.processing-steps .step {
    margin: 8px 0;
    display: flex;
    align-items: center;
    gap: 8px;
}

.processing-steps .step.active {
    color: var(--accent-color);
    font-weight: 600;
}

.processing-steps .step.done {
    color: #30d158;
}
</style>

<!-- iOS 状态栏颜色适配 -->
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
""", unsafe_allow_html=True)

# ========== 标题 ==========
st.markdown('<p class="big-title">🎙️ AI语音简报助手</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">语音直接转文字，自动生成简报</p>', unsafe_allow_html=True)

# ========== API 密钥管理（主界面） ==========
api_key = st.session_state.get("api_key", "")

if not api_key:
    st.warning("⚠️ 首次使用需要输入 API 密钥")
    
    with st.expander("🔑 点击此处输入 API 密钥", expanded=True):
        st.markdown("""
        **获取步骤：**
        1. 访问 [硅基流动](https://cloud.siliconflow.cn/i/nZqCjymq )
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
    st.caption("💡 AI简报_分享版 v2.2.0")

# ========== 语音转文字函数（修复版） ==========
def transcribe_audio(audio_bytes, api_key):
    tmp_path = None
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://api.siliconflow.cn/v1"
        )
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_bytes)
            tmp_path = tmp_file.name
        
        with open(tmp_path, "rb") as audio:
            transcription = client.audio.transcriptions.create(
                model="FunAudioLLM/SenseVoiceSmall",
                file=audio,
                response_format="text"
            )
            
            # 处理返回结果
            result_text = ""
            
            # 情况1：如果是对象，获取 text 属性
            if hasattr(transcription, 'text'):
                result_text = transcription.text
            
            # 情况2：如果是字符串
            elif isinstance(transcription, str):
                result_text = transcription.strip()
                
                # 尝试解析 JSON 格式 {"text": "..."}
                if result_text.startswith('{') and result_text.endswith('}'):
                    try:
                        json_data = json.loads(result_text)
                        if 'text' in json_data:
                            result_text = json_data['text']
                    except json.JSONDecodeError:
                        pass  # 不是有效 JSON，保持原样
                
                # 去除 text= 前缀
                elif result_text.lower().startswith('text='):
                    result_text = result_text[5:]
            
            # 情况3：其他类型，转为字符串
            else:
                result_text = str(transcription)
            
            # 最终清理
            result_text = result_text.strip().strip("'\"").strip()
            
            # 如果结果就是 "text" 这个词，返回空
            if result_text.lower() == 'text':
                result_text = ""
        
        return {"success": True, "text": result_text}
        
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ========== 计算预估处理时间 ==========
def estimate_processing_time(audio_bytes):
    """估算处理时间（秒）"""
    # 假设处理速度约为 10KB/秒
    bytes_per_second = 10240
    estimated_seconds = len(audio_bytes) / bytes_per_second
    # 最少3秒，最多60秒
    return max(3, min(int(estimated_seconds), 60))

def format_file_size(bytes_val):
    """格式化文件大小"""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.2f} MB"

# ========== 主界面 ==========
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎤 语音输入")
    
    # 方式一：实时录音
    st.markdown("""
    <div style="padding: 15px; border-radius: 12px; margin-bottom: 10px; 
                background-color: var(--bg-secondary); 
                border: 1px solid var(--border-color);">
        <h4 style="margin-top: 0; color: var(--text-primary);">方式一：实时录音</h4>
        <p style="color: var(--text-secondary); font-size: 14px; margin: 0;">
            📱 iPhone 提示：请使用 Safari 浏览器<br>
            点击录音 → 开始说话<br> 
            点击停止 → 自动转写
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        from streamlit_mic_recorder import mic_recorder
        
        audio = mic_recorder(
            start_prompt="🎙️ 点击录音",
            stop_prompt="⏹️ 点击停止",
            just_once=True,
            key="mic_recorder_ios_v2"
        )
        
        if audio and audio.get("bytes"):
            audio_bytes = audio["bytes"]
            file_size = format_file_size(len(audio_bytes))
            est_time = estimate_processing_time(audio_bytes)
            
            # 显示处理提示
            st.markdown(f"""
            <div class="processing-hint">
                🎙️ 录音已停止，准备转写...<br>
                <small>📦 {file_size} · ⏱️ 预计需要 {est_time} 秒</small>
            </div>
            <div class="processing-steps">
                <div class="step done">✓ 完成录音</div>
                <div class="step active">⟳ 正在转写（请耐心等待）...</div>
                <div class="step">○ 等待生成</div>
            </div>
            """, unsafe_allow_html=True)
            
            # 使用 spinner 显示详细进度
            with st.spinner(f"🤖 AI正在转写中...（{file_size}，预计{est_time}秒）"):
                result = transcribe_audio(audio_bytes, api_key)
                
                if result["success"]:
                    # 检查清理后的文本是否有效
                    clean_text = result["text"]
                    if not clean_text or clean_text.strip() == "":
                        st.warning("⚠️ 转写结果为空，请检查录音是否清晰")
                    else:
                        st.session_state.transcribed_text = clean_text
                        st.success(f"✅ 转写完成！共 {len(clean_text)} 字")
                        st.rerun()
                else:
                    st.error(f"❌ 转写失败：{result['error']}")
                    
    except ImportError:
        st.error("⚠️ 录音组件加载失败，请使用方式二上传文件")
    except Exception as e:
        st.error(f"⚠️ 录音功能异常：{str(e)}")
        st.info("请尝试使用方式二上传录音文件")
    
    st.divider()
    
    # 方式二：上传录音（iOS 推荐）
    st.subheader("📁 方式二：上传录音")
    
    st.info("""
    💡 **iPhone 用户推荐此方式**：
    1. 用"语音备忘录"录好音
    2. 点击分享 → 存储到"文件"
    3. 在这里选择文件上传
    """)
    
    audio_file = st.file_uploader(
        "选择录音文件", 
        type=['mp3', 'wav', 'm4a', 'webm', 'ogg'],
        help="支持 mp3, wav, m4a, webm, ogg 格式"
    )
    
    if audio_file:
        audio_bytes = audio_file.getvalue()
        file_size = format_file_size(len(audio_bytes))
        est_time = estimate_processing_time(audio_bytes)
        
        st.audio(audio_file, format=f'audio/{audio_file.type.split("/")[1]}')
        
        # 显示文件信息和预估时间
        st.info(f"📦 文件大小：**{file_size}** · ⏱️ 预计处理时间：**约{est_time}秒**")
        
        if st.button("🎯 开始转写", type="primary", key="transcribe_upload"):
            # 显示处理提示
            st.markdown(f"""
            <div class="processing-hint">
                🚀 开始处理音频文件...<br>
                <small>📦 {file_size} · ⏱️ 预计需要 {est_time} 秒，请耐心等待</small>
            </div>
            <div class="processing-steps">
                <div class="step done">✓ 上传完成</div>
                <div class="step active">⟳ AI正在识别（请勿关闭页面）...</div>
                <div class="step">○ 等待结果</div>
            </div>
            """, unsafe_allow_html=True)
            
            with st.spinner(f"🤖 正在识别中...（{file_size}，预计{est_time}秒，请耐心等待）"):
                result = transcribe_audio(audio_bytes, api_key)
                
                if result["success"]:
                    clean_text = result["text"]
                    if not clean_text or clean_text.strip() == "":
                        st.warning("⚠️ 转写结果为空，请检查音频文件")
                    else:
                        st.session_state.transcribed_text = clean_text
                        st.success(f"✅ 完成！共 {len(clean_text)} 字")
                        st.rerun()
                else:
                    st.error(f"❌ 失败：{result['error']}")

with col2:
    st.subheader("📝 编辑与生成")
    
    briefing_type = st.selectbox(
        "简报类型",
        ["会议纪要", "工作日报", "学习笔记", "新闻摘要"],
        key="briefing_type"
    )
    
    default_text = st.session_state.get("transcribed_text", "")
    
    content = st.text_area(
        "编辑内容",
        value=default_text,
        height=300,
        placeholder="语音转写内容会出现在这里，您也可以直接输入..."
    )
    
    if content != st.session_state.get("transcribed_text", ""):
        st.session_state.transcribed_text = content
    
    custom_req = st.text_input("特殊要求", placeholder="例如：重点突出数据、使用 bullet points")
    
    col_gen, col_clear = st.columns([3, 1])
    with col_gen:
        if st.button("✨ 生成简报", type="primary", use_container_width=True):
            if not content.strip():
                st.error("❌ 内容不能为空")
            else:
                with st.spinner("🤖 生成中..."):
                    try:
                        client = OpenAI(
                            api_key=api_key, 
                            base_url="https://api.siliconflow.cn/v1"
                        )
                        
                        prompts = {
                            "会议纪要": "整理成会议纪要：1主题 2讨论 3决议 4待办",
                            "工作日报": "整理成工作日报：1完成 2问题 3计划",
                            "学习笔记": "整理成学习笔记：1概念 2重点 3思考",
                            "新闻摘要": "整理成新闻摘要：1事件 2数据 3影响"
                        }
                        
                        prompt = prompts[briefing_type]
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
                        
                    except Exception as e:
                        st.error(f"❌ 生成失败：{str(e)}")
    
    with col_clear:
        if st.button("🗑️ 清空", use_container_width=True):
            st.session_state.transcribed_text = ""
            if "generated_result" in st.session_state:
                del st.session_state.generated_result
            st.rerun()
    
    if "generated_result" in st.session_state:
        st.divider()
        st.success("✅ 生成完成！")
        st.markdown(st.session_state.generated_result)
        st.download_button(
            "📋 下载",
            st.session_state.generated_result,
            file_name=f"简报_{briefing_type}.txt",
            mime="text/plain"
        )

st.divider()
st.caption("Made with ❤️ | 语音版v2.2.0 - iOS 自动暗黑模式")
