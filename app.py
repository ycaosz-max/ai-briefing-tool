import streamlit as st
from openai import OpenAI
import os
import tempfile
import wave
import io

# ========== 页面设置 ==========
st.set_page_config(
    page_title="AI语音简报助手", 
    page_icon="🎙️",
    initial_sidebar_state="auto"
)

# ========== iOS 暗黑/明亮模式自动切换 + 录音计时器样式 ==========
st.markdown("""
<style>
/* ========== CSS 变量定义 ========== */
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f0f2f6;
    --bg-card: #ffffff;
    --text-primary: #1f1f1f;
    --text-secondary: #666666;
    --border-color: #e0e0e0;
    --accent-color: #ff4b4b;
    --accent-hover: #ff3333;
    --timer-bg: rgba(255, 75, 75, 0.95);
    --timer-text: #ffffff;
    --shadow: rgba(0, 0, 0, 0.2);
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
        --timer-bg: rgba(10, 132, 255, 0.95);
        --timer-text: #ffffff;
        --shadow: rgba(0, 0, 0, 0.5);
    }
    
    .stApp { background-color: var(--bg-primary) !important; }
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

/* ========== 基础样式 ========== */
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

/* ========== 录音计时器样式 ========== */
.recording-timer {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    background: var(--timer-bg);
    color: var(--timer-text);
    padding: 30px 50px;
    border-radius: 20px;
    font-size: 48px;
    font-weight: bold;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', monospace;
    z-index: 999999;
    box-shadow: 0 10px 40px var(--shadow);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
    display: none;
    flex-direction: column;
    align-items: center;
    gap: 10px;
    border: 2px solid rgba(255,255,255,0.2);
}

.recording-timer.active {
    display: flex;
    animation: pulse 2s infinite;
}

.recording-timer .timer-label {
    font-size: 14px;
    opacity: 0.9;
    text-transform: uppercase;
    letter-spacing: 2px;
}

.recording-timer .timer-display {
    font-variant-numeric: tabular-nums;
    letter-spacing: 2px;
}

@keyframes pulse {
    0%, 100% { 
        transform: translate(-50%, -50%) scale(1);
        box-shadow: 0 10px 40px var(--shadow);
    }
    50% { 
        transform: translate(-50%, -50%) scale(1.02);
        box-shadow: 0 15px 50px var(--shadow);
    }
}

/* 录音指示器红点 */
.recording-indicator {
    width: 12px;
    height: 12px;
    background: #ff453a;
    border-radius: 50%;
    display: inline-block;
    margin-right: 8px;
    animation: blink 1s infinite;
}

@keyframes blink {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.3; }
}

/* ========== 输入框和按钮样式 ========== */
.stTextInput input, .stTextArea textarea {
    -webkit-appearance: none !important;
    -webkit-user-select: text !important;
    user-select: text !important;
    font-size: 16px !important;
    touch-action: manipulation;
    -webkit-border-radius: 10px;
    border-radius: 10px;
    background-color: var(--bg-card);
    color: var(--text-primary);
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
    -webkit-border-radius: 10px;
    border-radius: 10px;
    background-color: var(--accent-color) !important;
    color: #ffffff !important;
    border: none !important;
    font-weight: 600;
    transition: all 0.2s ease;
}

.stButton button:hover {
    background-color: var(--accent-hover) !important;
    transform: translateY(-1px);
}

/* ========== 响应式适配 ========== */
@media (max-width: 768px) {
    .big-title { font-size: 26px !important; }
    .subtitle { font-size: 14px !important; }
    .main .block-container { padding: 1rem; }
    .stApp { padding-bottom: env(safe-area-inset-bottom); }
    
    .recording-timer {
        padding: 20px 35px;
        font-size: 36px;
    }
    .recording-timer .timer-label {
        font-size: 12px;
    }
}

/* 平滑过渡 */
* {
    transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease;
}
</style>

<!-- 录音计时器 HTML 结构 -->
<div id="recording-timer" class="recording-timer">
    <div class="timer-label"><span class="recording-indicator"></span>正在录音</div>
    <div class="timer-display" id="timer-display">00:00</div>
</div>

<!-- 计时器 JavaScript -->
<script>
(function() {
    let timerInterval = null;
    let startTime = null;
    let isRecording = false;
    
    // 格式化时间显示
    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
        const secs = (seconds % 60).toString().padStart(2, '0');
        return mins + ':' + secs;
    }
    
    // 开始计时
    function startTimer() {
        if (isRecording) return;
        isRecording = true;
        startTime = Date.now();
        
        const timerEl = document.getElementById('recording-timer');
        const displayEl = document.getElementById('timer-display');
        
        timerEl.classList.add('active');
        
        // 立即更新一次
        displayEl.textContent = '00:00';
        
        // 每秒更新
        timerInterval = setInterval(function() {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            displayEl.textContent = formatTime(elapsed);
        }, 1000);
        
        console.log('🎙️ 录音计时开始');
    }
    
    // 停止计时
    function stopTimer() {
        if (!isRecording) return;
        isRecording = false;
        
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
        
        const timerEl = document.getElementById('recording-timer');
        const elapsed = Math.floor((Date.now() - startTime) / 1000);
        
        // 保存时长到 sessionStorage，供 Python 读取
        sessionStorage.setItem('last_recording_duration', elapsed);
        sessionStorage.setItem('last_recording_timestamp', Date.now());
        
        // 隐藏计时器
        timerEl.classList.remove('active');
        
        console.log('⏹️ 录音计时停止，时长：' + formatTime(elapsed));
        
        // 显示完成提示
        showCompletionNotice(elapsed);
    }
    
    // 显示完成提示
    function showCompletionNotice(seconds) {
        const notice = document.createElement('div');
        notice.style.cssText = `
            position: fixed;
            top: 20%;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(48, 209, 88, 0.95);
            color: white;
            padding: 15px 30px;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            z-index: 999999;
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
            animation: slideDown 0.3s ease;
        `;
        notice.innerHTML = '✅ 录音完成 | 时长：' + formatTime(seconds);
        document.body.appendChild(notice);
        
        setTimeout(function() {
            notice.style.opacity = '0';
            notice.style.transition = 'opacity 0.5s';
            setTimeout(function() {
                if (notice.parentNode) notice.parentNode.removeChild(notice);
            }, 500);
        }, 3000);
    }
    
    // 监听按钮文字变化
    function setupButtonObserver() {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                const buttons = document.querySelectorAll('button');
                buttons.forEach(function(btn) {
                    const text = btn.textContent || '';
                    
                    // 检测开始录音（包含麦克风图标）
                    if (text.includes('🎙️') && text.includes('开始录音') && !isRecording) {
                        // 延迟一点确保是真的开始了
                        setTimeout(function() {
                            if (btn.textContent.includes('停止')) {
                                startTimer();
                            }
                        }, 100);
                    }
                    
                    // 检测停止录音
                    if (text.includes('⏹️') && text.includes('停止') && isRecording) {
                        // 这是停止按钮，我们监听点击
                        if (!btn._hasClickListener) {
                            btn._hasClickListener = true;
                            btn.addEventListener('click', function() {
                                setTimeout(stopTimer, 100);
                            });
                        }
                    }
                });
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            characterData: true
        });
        
        // 也定期检查按钮状态（备用方案）
        setInterval(function() {
            const stopBtn = Array.from(document.querySelectorAll('button')).find(
                b => b.textContent.includes('⏹️') && b.textContent.includes('停止')
            );
            if (stopBtn && !stopBtn._hasClickListener) {
                stopBtn._hasClickListener = true;
                stopBtn.addEventListener('click', function() {
                    setTimeout(stopTimer, 100);
                });
            }
        }, 500);
    }
    
    // 添加动画样式
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideDown {
            from { transform: translateX(-50%) translateY(-20px); opacity: 0; }
            to { transform: translateX(-50%) translateY(0); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
    
    // 初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupButtonObserver);
    } else {
        setupButtonObserver();
    }
    
    // 暴露全局函数供 Streamlit 调用
    window.getRecordingDuration = function() {
        const duration = sessionStorage.getItem('last_recording_duration');
        const timestamp = sessionStorage.getItem('last_recording_timestamp');
        // 5秒内的数据才有效
        if (duration && timestamp && (Date.now() - timestamp < 5000)) {
            sessionStorage.removeItem('last_recording_duration');
            sessionStorage.removeItem('last_recording_timestamp');
            return parseInt(duration);
        }
        return null;
    };
})();
</script>

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
        
        with col2:
            st.caption("💡 或设置环境变量 `SILICONFLOW_API_KEY`")
    
    st.stop()

# ========== 侧边栏 ==========
with st.sidebar:
    st.header("⚙️ 设置")
    st.success("✅ API 已配置")
    
    if st.button("🔄 更换 API 密钥"):
        del st.session_state.api_key
        st.rerun()
    
    st.divider()
    st.caption("💡 AI简报_分享版 v2.3.0")

# ========== 计算音频时长函数 ==========
def get_audio_duration(audio_bytes):
    """通过音频文件计算时长"""
    try:
        # 尝试作为 WAV 文件读取
        with io.BytesIO(audio_bytes) as buf:
            with wave.open(buf, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
                return duration
    except:
        # 如果不是 WAV 格式，估算（假设为 16kHz, 16bit, 单声道）
        # 每秒 = 32000 字节 (16000 * 2)
        estimated = len(audio_bytes) / 32000
        return estimated

def format_duration(seconds):
    """格式化为 MM:SS"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"

# ========== 语音转文字函数 ==========
def transcribe_audio(audio_bytes, api_key):
    tmp_path = None
    try:
        # 计算录音时长
        duration = get_audio_duration(audio_bytes)
        
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
        
        return {
            "success": True, 
            "text": transcription,
            "duration": duration
        }
        
    except Exception as e:
        return {
            "success": False, 
            "error": str(e),
            "duration": 0
        }
    
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

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
            点击录音 → 屏幕中央显示计时器 → 点击停止自动转写
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        from streamlit_mic_recorder import mic_recorder
        
        audio = mic_recorder(
            start_prompt="🎙️ 点击开始录音",
            stop_prompt="⏹️ 点击停止",
            just_once=True,
            key="mic_recorder_ios_v3"
        )
        
        if audio and audio.get("bytes"):
            # 计算录音时长
            duration = get_audio_duration(audio["bytes"])
            duration_str = format_duration(duration)
            
            with st.spinner(f"🤖 AI正在转写... (录音时长: {duration_str})"):
                result = transcribe_audio(audio["bytes"], api_key)
                
                if result["success"]:
                    st.session_state.transcribed_text = result["text"]
                    st.session_state.last_duration = result["duration"]
                    
                    # 显示成功信息（包含字数和时长）
                    word_count = len(result["text"])
                    st.success(f"✅ 转写完成！共 {word_count} 字 | 录音时长：{format_duration(result['duration'])}")
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
        st.audio(audio_file, format=f'audio/{audio_file.type.split("/")[1]}')
        
        if st.button("🎯 开始转写", type="primary", key="transcribe_upload"):
            with st.spinner("🤖 正在识别..."):
                result = transcribe_audio(audio_file.getvalue(), api_key)
                
                if result["success"]:
                    st.session_state.transcribed_text = result["text"]
                    st.session_state.last_duration = result["duration"]
                    
                    word_count = len(result["text"])
                    st.success(f"✅ 完成！共 {word_count} 字 | 录音时长：{format_duration(result['duration'])}")
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
    
    # 显示上次录音时长（如果有）
    if "last_duration" in st.session_state:
        st.caption(f"⏱️ 上次录音时长: {format_duration(st.session_state.last_duration)}")
    
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
            if "last_duration" in st.session_state:
                del st.session_state.last_duration
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
st.caption("Made with ❤️ | 语音版v2.3.0 - 实时录音计时器")
