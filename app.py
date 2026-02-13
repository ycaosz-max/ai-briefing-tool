import streamlit as st
from openai import OpenAI
import os
import tempfile

# ========== 页面设置 ==========
st.set_page_config(
    page_title="AI语音简报助手", 
    page_icon="🎙️",
    initial_sidebar_state="auto"
)

# ========== iOS 暗黑/明亮模式 + 实时字节数显示 ==========
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
    --shadow: rgba(0, 0, 0, 0.1);
    --input-bg: #ffffff;
    --input-text: #1f1f1f;
    --button-text: #ffffff;
    --timer-bg: #ff3b30;
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
        --shadow: rgba(0, 0, 0, 0.5);
        --input-bg: #1c1c1e;
        --input-text: #ffffff;
        --button-text: #ffffff;
        --timer-bg: #0a84ff;
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

/* ========== 实时录音状态栏（底部固定） ========== */
.recording-status-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: var(--timer-bg);
    color: white;
    padding: 15px 20px;
    z-index: 999999;
    transform: translateY(100%);
    transition: transform 0.3s ease;
    display: flex;
    justify-content: space-around;
    align-items: center;
    font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    box-shadow: 0 -5px 20px rgba(0,0,0,0.3);
    padding-bottom: max(15px, env(safe-area-inset-bottom));
}

.recording-status-bar.active {
    transform: translateY(0);
}

.status-item {
    text-align: center;
    flex: 1;
}

.status-item .label {
    font-size: 11px;
    opacity: 0.8;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 4px;
}

.status-item .value {
    font-size: 20px;
    font-weight: bold;
    font-variant-numeric: tabular-nums;
}

.status-item .unit {
    font-size: 12px;
    opacity: 0.7;
    margin-left: 2px;
}

.pulse-dot {
    width: 10px;
    height: 10px;
    background: white;
    border-radius: 50%;
    animation: blink 1s infinite;
    display: inline-block;
    margin-right: 5px;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* 其他样式 */
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

.stExpander {
    background-color: var(--bg-card);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    overflow: hidden;
    transition: all 0.3s ease;
}

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

.stFileUploader > div > div {
    background-color: var(--bg-secondary) !important;
    border-color: var(--border-color) !important;
    color: var(--text-primary) !important;
}

[data-testid="stSidebar"] {
    background-color: var(--bg-secondary) !important;
}

@media (max-width: 768px) {
    .big-title { font-size: 26px !important; }
    .subtitle { font-size: 14px !important; }
    .main .block-container { padding: 1rem; }
    .stApp { padding-bottom: env(safe-area-inset-bottom); }
    .status-item .value { font-size: 16px; }
    .status-item .label { font-size: 10px; }
}

* {
    transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}
</style>

<!-- 实时录音状态栏 -->
<div id="recording-status" class="recording-status-bar">
    <div class="status-item">
        <div class="label"><span class="pulse-dot"></span>录音状态</div>
        <div class="value" style="font-size: 14px;">录制中</div>
    </div>
    <div class="status-item">
        <div class="label">时长</div>
        <div class="value"><span id="timer-val">00:00</span></div>
    </div>
    <div class="status-item">
        <div class="label">估算大小</div>
        <div class="value"><span id="bytes-val">0</span><span class="unit">KB</span></div>
    </div>
</div>

<script>
(function() {
    'use strict';
    
    let timerInterval = null;
    let startTime = null;
    let isRecording = false;
    
    // 音频参数估算（16kHz, 16bit, 单声道 = 32KB/秒）
    const BYTES_PER_SECOND = 32000;
    
    function formatTime(seconds) {
        const m = Math.floor(seconds / 60).toString().padStart(2, '0');
        const s = (seconds % 60).toString().padStart(2, '0');
        return m + ':' + s;
    }
    
    function formatBytes(bytes) {
        if (bytes < 1024) return bytes;
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1);
        return (bytes / (1024 * 1024)).toFixed(2) + ' MB';
    }
    
    function updateDisplay() {
        if (!startTime) return;
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const bytes = elapsed * BYTES_PER_SECOND;
        
        const timerEl = document.getElementById('timer-val');
        const bytesEl = document.getElementById('bytes-val');
        
        if (timerEl) timerEl.textContent = formatTime(elapsed);
        if (bytesEl) {
            if (bytes < 1024 * 1024) {
                bytesEl.textContent = (bytes / 1024).toFixed(1);
                bytesEl.nextElementSibling.textContent = 'KB';
            } else {
                bytesEl.textContent = (bytes / (1024 * 1024)).toFixed(2);
                bytesEl.nextElementSibling.textContent = 'MB';
            }
        }
    }
    
    function startRecording() {
        if (isRecording) return;
        isRecording = true;
        startTime = Date.now();
        
        const statusBar = document.getElementById('recording-status');
        if (statusBar) statusBar.classList.add('active');
        
        updateDisplay();
        timerInterval = setInterval(updateDisplay, 1000);
        
        // 保存到 localStorage
        localStorage.setItem('rec_start', startTime.toString());
        localStorage.setItem('is_recording', 'true');
        
        console.log('[Record] Started');
    }
    
    function stopRecording() {
        if (!isRecording) return;
        isRecording = false;
        
        clearInterval(timerInterval);
        
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        const bytes = elapsed * BYTES_PER_SECOND;
        
        const statusBar = document.getElementById('recording-status');
        if (statusBar) statusBar.classList.remove('active');
        
        // 保存结果
        localStorage.setItem('rec_duration', elapsed.toString());
        localStorage.setItem('rec_bytes', bytes.toString());
        localStorage.setItem('is_recording', 'false');
        localStorage.setItem('rec_finished', Date.now().toString());
        
        console.log('[Record] Stopped. Duration:', elapsed, 's, Bytes:', bytes);
        
        // 更新 URL 让 Python 获取
        const url = new URL(window.location.href);
        url.searchParams.set('dur', elapsed);
        url.searchParams.set('bytes', bytes);
        url.searchParams.set('t', Date.now());
        window.history.replaceState({}, '', url);
        
        showCompletion(elapsed, bytes);
    }
    
    function showCompletion(seconds, bytes) {
        let sizeStr;
        if (bytes < 1024 * 1024) {
            sizeStr = (bytes / 1024).toFixed(1) + ' KB';
        } else {
            sizeStr = (bytes / (1024 * 1024)).toFixed(2) + ' MB';
        }
        
        const div = document.createElement('div');
        div.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #34c759;
            color: white;
            padding: 25px 35px;
            border-radius: 16px;
            text-align: center;
            z-index: 1000000;
            font-family: -apple-system, sans-serif;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
            min-width: 200px;
        `;
        div.innerHTML = `
            <div style="font-size: 40px; margin-bottom: 8px;">✓</div>
            <div style="font-size: 18px; font-weight: bold;">录音完成</div>
            <div style="font-size: 14px; margin-top: 8px; opacity: 0.9;">
                ${formatTime(seconds)} · ${sizeStr}
            </div>
        `;
        document.body.appendChild(div);
        
        setTimeout(() => {
            div.style.opacity = '0';
            div.style.transition = 'opacity 0.5s';
            setTimeout(() => div.remove(), 500);
        }, 2500);
    }
    
    // 恢复录音状态（页面刷新后）
    function restoreState() {
        const wasRecording = localStorage.getItem('is_recording');
        const start = localStorage.getItem('rec_start');
        
        if (wasRecording === 'true' && start) {
            const elapsed = Math.floor((Date.now() - parseInt(start)) / 1000);
            if (elapsed < 300) { // 5分钟内
                isRecording = true;
                startTime = parseInt(start);
                
                const statusBar = document.getElementById('recording-status');
                if (statusBar) statusBar.classList.add('active');
                
                updateDisplay();
                timerInterval = setInterval(updateDisplay, 1000);
            }
        }
    }
    
    // 监听所有按钮点击
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('button');
        if (!btn) return;
        
        const text = btn.textContent || '';
        
        // 开始录音
        if (text.includes('🎙️') || text.includes('开始录音')) {
            setTimeout(startRecording, 50);
        }
        
        // 停止录音
        if (text.includes('⏹️') || text.includes('停止')) {
            setTimeout(stopRecording, 50);
        }
    }, true);
    
    // 初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', restoreState);
    } else {
        restoreState();
    }
})();
</script>

<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="theme-color" content="#000000" media="(prefers-color-scheme: dark)">
<meta name="theme-color" content="#ffffff" media="(prefers-color-scheme: light)">
""", unsafe_allow_html=True)

# ========== 标题 ==========
st.markdown('<p class="big-title">🎙️ AI语音简报助手</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">语音直接转文字，自动生成简报</p>', unsafe_allow_html=True)

# ========== 从 URL 读取录音数据 ==========
query_params = st.query_params
recording_info = {}
if 'dur' in query_params and 'bytes' in query_params:
    try:
        recording_info = {
            'duration': int(query_params['dur']),
            'bytes': int(query_params['bytes'])
        }
        # 清理 URL
        del st.query_params['dur']
        del st.query_params['bytes']
    except:
        pass

# ========== API 密钥管理 ==========
api_key = st.session_state.get("api_key", "")

if not api_key:
    st.warning("⚠️ 首次使用需要输入 API 密钥")
    
    with st.expander("🔑 点击此处输入 API 密钥", expanded=True):
        st.markdown("""
        **获取步骤：**
        1. 访问 [硅基流动](https://cloud.siliconflow.cn/i/nZqCjymq)
        2. 注册并完成实名认证
        3. 创建您的 API 密钥
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
    st.caption("💡 AI简报_分享版 v2.6.0")

# ========== 工具函数 ==========
def format_bytes(bytes_val):
    """格式化字节数"""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.2f} MB"

def format_duration(seconds):
    """格式化为 MM:SS"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

# ========== 语音转文字函数 ==========
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
        
        return {"success": True, "text": transcription}
        
    except Exception as e:
        return {"success": False, "error": str(e)}
    
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ========== 主界面 ==========
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎤 语音输入")
    
    # 显示上次录音信息
    if recording_info:
        st.info(f"⏱️ 上次录音：**{format_duration(recording_info['duration'])}** · 📦 **{format_bytes(recording_info['bytes'])}**")
    
    # 方式一：实时录音
    st.markdown("""
    <div style="padding: 15px; border-radius: 12px; margin-bottom: 10px; 
                background-color: var(--bg-secondary); 
                border: 1px solid var(--border-color);">
        <h4 style="margin-top: 0; color: var(--text-primary);">方式一：实时录音</h4>
        <p style="color: var(--text-secondary); font-size: 14px; margin: 0;">
            📱 点击开始 → 底部显示<strong>实时时长和估算大小</strong> → 点击停止<br>
            <span style="opacity: 0.7;">基于 16kHz/16bit 单声道音频估算</span>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        from streamlit_mic_recorder import mic_recorder
        
        audio = mic_recorder(
            start_prompt="🎙️ 点击开始录音",
            stop_prompt="⏹️ 点击停止",
            just_once=True,
            key="mic_recorder_bytes_v1"
        )
        
        if audio and audio.get("bytes"):
            actual_bytes = len(audio["bytes"])
            
            with st.spinner("🤖 AI正在转写..."):
                result = transcribe_audio(audio["bytes"], api_key)
                
                if result["success"]:
                    st.session_state.transcribed_text = result["text"]
                    word_count = len(result["text"])
                    
                    # 显示实际字节数对比
                    info_cols = st.columns(2)
                    with info_cols[0]:
                        st.metric("实际大小", format_bytes(actual_bytes))
                    with info_cols[1]:
                        st.metric("转写字数", f"{word_count} 字")
                    
                    st.success(f"✅ 转写完成！")
                    st.rerun()
                else:
                    st.error(f"❌ 转写失败：{result['error']}")
                    
    except ImportError:
        st.error("⚠️ 录音组件加载失败，请使用方式二上传文件")
    except Exception as e:
        st.error(f"⚠️ 录音功能异常：{str(e)}")
        st.info("请尝试使用方式二上传录音文件")
    
    st.divider()
    
    # 方式二：上传录音
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
        file_size = len(audio_file.getvalue())
        st.caption(f"📦 文件大小：**{format_bytes(file_size)}**")
        st.audio(audio_file, format=f'audio/{audio_file.type.split("/")[1]}')
        
        if st.button("🎯 开始转写", type="primary", key="transcribe_upload"):
            with st.spinner("🤖 正在识别..."):
                result = transcribe_audio(audio_file.getvalue(), api_key)
                
                if result["success"]:
                    st.session_state.transcribed_text = result["text"]
                    word_count = len(result["text"])
                    st.success(f"✅ 完成！共 {word_count} 字")
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
st.caption("Made with ❤️ | 语音版v2.6.0 - 实时字节估算")
