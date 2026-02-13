import streamlit as st
from openai import OpenAI
import os
import tempfile
import time

# ========== 页面设置 ==========
st.set_page_config(
    page_title="AI语音简报助手", 
    page_icon="🎙️",
    initial_sidebar_state="auto"
)

# ========== 初始化 Session State ==========
if 'recording' not in st.session_state:
    st.session_state.recording = False
if 'recording_start' not in st.session_state:
    st.session_state.recording_start = 0
if 'recording_duration' not in st.session_state:
    st.session_state.recording_duration = 0
if 'audio_processed' not in st.session_state:
    st.session_state.audio_processed = False

# ========== CSS + JavaScript 计时器（iOS 优化版） ==========
st.markdown("""
<style>
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f0f2f6;
    --text-primary: #1f1f1f;
    --accent-color: #ff4b4b;
    --timer-bg: #ff3b30;
    --timer-text: #ffffff;
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg-primary: #000000;
        --bg-secondary: #1c1c1e;
        --text-primary: #ffffff;
        --accent-color: #0a84ff;
        --timer-bg: #0a84ff;
    }
    .stApp { background-color: #000000 !important; }
}

* {
    -webkit-tap-highlight-color: transparent;
    -webkit-touch-callout: none;
    -webkit-user-select: none;
    user-select: none;
}

.stApp {
    background-color: var(--bg-primary);
    color: var(--text-primary);
}

/* ========== 录音计时器 - 固定底部（iOS 友好） ========== */
.ios-timer-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: var(--timer-bg);
    color: var(--timer-text);
    padding: 20px;
    text-align: center;
    z-index: 999999;
    transform: translateY(100%);
    transition: transform 0.3s ease;
    box-shadow: 0 -5px 20px rgba(0,0,0,0.3);
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 15px;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    padding-bottom: max(20px, env(safe-area-inset-bottom));
}

.ios-timer-bar.active {
    transform: translateY(0);
}

.ios-timer-bar .pulse-dot {
    width: 12px;
    height: 12px;
    background: white;
    border-radius: 50%;
    animation: pulse-animation 1s infinite;
}

.ios-timer-bar .timer-text {
    font-size: 24px;
    font-weight: bold;
    font-variant-numeric: tabular-nums;
    letter-spacing: 2px;
}

.ios-timer-bar .timer-label {
    font-size: 14px;
    opacity: 0.9;
    text-transform: uppercase;
}

@keyframes pulse-animation {
    0%, 100% { opacity: 1; transform: scale(1); }
    50% { opacity: 0.5; transform: scale(0.8); }
}

/* 中央大计时器（备用） */
.center-timer {
    position: fixed;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%) scale(0);
    background: var(--timer-bg);
    color: white;
    padding: 40px;
    border-radius: 20px;
    text-align: center;
    z-index: 1000000;
    transition: transform 0.3s ease;
    box-shadow: 0 10px 40px rgba(0,0,0,0.4);
}

.center-timer.active {
    transform: translate(-50%, -50%) scale(1);
}

.center-timer .big-time {
    font-size: 56px;
    font-weight: bold;
    font-family: monospace;
    margin: 10px 0;
}

/* 其他样式 */
.big-title {
    font-size: 28px;
    font-weight: bold;
    color: var(--text-primary);
    margin-bottom: 8px;
}

.subtitle {
    font-size: 15px;
    color: var(--text-secondary);
    margin-bottom: 20px;
}

.stButton button {
    -webkit-appearance: none;
    border-radius: 12px;
    background-color: var(--accent-color) !important;
    color: white !important;
    font-weight: 600;
    font-size: 16px;
    padding: 12px 24px;
    width: 100%;
    border: none;
    margin: 5px 0;
}

/* 录音中按钮样式 */
.recording-active button {
    background-color: #ff3b30 !important;
    animation: button-pulse 2s infinite;
}

@keyframes button-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
}

/* 信息卡片 */
.info-card {
    background: var(--bg-secondary);
    padding: 15px;
    border-radius: 12px;
    margin: 10px 0;
    border: 1px solid var(--border-color);
}

/* 移动端优化 */
@media (max-width: 768px) {
    .big-title { font-size: 24px; }
    .center-timer .big-time { font-size: 40px; }
    .ios-timer-bar .timer-text { font-size: 20px; }
}
</style>

<!-- iOS 计时器 HTML -->
<div id="ios-timer-bar" class="ios-timer-bar">
    <div class="pulse-dot"></div>
    <div>
        <div class="timer-text" id="timer-display">00:00</div>
        <div class="timer-label">正在录音 · 点击停止按钮结束</div>
    </div>
</div>

<!-- 中央备用计时器 -->
<div id="center-timer" class="center-timer">
    <div style="font-size: 48px;">🔴</div>
    <div class="big-time" id="center-time">00:00</div>
    <div style="font-size: 14px; opacity: 0.8;">录音中...</div>
</div>

<script>
// iOS 优化的计时器逻辑
(function() {
    'use strict';
    
    let timerInterval = null;
    let startTime = null;
    
    function formatTime(sec) {
        const m = Math.floor(sec / 60).toString().padStart(2, '0');
        const s = (sec % 60).toString().padStart(2, '0');
        return m + ':' + s;
    }
    
    function updateDisplay(seconds) {
        const timeStr = formatTime(seconds);
        const el1 = document.getElementById('timer-display');
        const el2 = document.getElementById('center-time');
        if (el1) el1.textContent = timeStr;
        if (el2) el2.textContent = timeStr;
    }
    
    function startTimer() {
        console.log('[Timer] Starting...');
        startTime = Date.now();
        
        // 显示底部计时器
        const bar = document.getElementById('ios-timer-bar');
        if (bar) bar.classList.add('active');
        
        // 同时显示中央计时器（确保可见）
        const center = document.getElementById('center-timer');
        if (center) center.classList.add('active');
        
        // 每秒更新
        updateDisplay(0);
        timerInterval = setInterval(function() {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            updateDisplay(elapsed);
        }, 1000);
        
        // 保存状态
        localStorage.setItem('is_recording', 'true');
        localStorage.setItem('recording_start', startTime.toString());
    }
    
    function stopTimer() {
        console.log('[Timer] Stopping...');
        if (timerInterval) {
            clearInterval(timerInterval);
            timerInterval = null;
        }
        
        const duration = startTime ? Math.floor((Date.now() - startTime) / 1000) : 0;
        
        // 隐藏计时器
        const bar = document.getElementById('ios-timer-bar');
        if (bar) bar.classList.remove('active');
        
        const center = document.getElementById('center-timer');
        if (center) center.classList.remove('active');
        
        // 保存时长
        localStorage.setItem('recording_duration', duration.toString());
        localStorage.setItem('is_recording', 'false');
        localStorage.setItem('recording_finished', Date.now().toString());
        
        console.log('[Timer] Duration:', duration);
        
        // 显示完成提示
        showDone(duration);
        
        return duration;
    }
    
    function showDone(seconds) {
        const div = document.createElement('div');
        div.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #34c759;
            color: white;
            padding: 30px 40px;
            border-radius: 16px;
            text-align: center;
            z-index: 1000001;
            font-family: -apple-system, sans-serif;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3);
        `;
        div.innerHTML = `
            <div style="font-size: 48px; margin-bottom: 10px;">✓</div>
            <div style="font-size: 20px; font-weight: bold;">录音完成</div>
            <div style="font-size: 32px; margin-top: 8px;">${formatTime(seconds)}</div>
        `;
        document.body.appendChild(div);
        
        setTimeout(function() {
            div.style.opacity = '0';
            div.style.transition = 'opacity 0.5s';
            setTimeout(function() { div.remove(); }, 500);
        }, 2000);
    }
    
    // 检查是否应该从 localStorage 恢复计时
    function checkRecordingState() {
        const isRecording = localStorage.getItem('is_recording');
        const start = localStorage.getItem('recording_start');
        
        if (isRecording === 'true' && start) {
            const elapsed = Math.floor((Date.now() - parseInt(start)) / 1000);
            if (elapsed < 300) { // 5分钟内
                console.log('[Timer] Restoring recording state, elapsed:', elapsed);
                startTime = parseInt(start);
                
                const bar = document.getElementById('ios-timer-bar');
                if (bar) bar.classList.add('active');
                const center = document.getElementById('center-timer');
                if (center) center.classList.add('active');
                
                updateDisplay(elapsed);
                timerInterval = setInterval(function() {
                    const e = Math.floor((Date.now() - startTime) / 1000);
                    updateDisplay(e);
                }, 1000);
            }
        }
    }
    
    // 监听按钮点击（使用事件委托，更可靠）
    document.addEventListener('click', function(e) {
        const btn = e.target.closest('button');
        if (!btn) return;
        
        const text = btn.textContent || '';
        
        // 点击开始录音
        if (text.includes('🎙️') || text.includes('开始录音')) {
            console.log('[Click] Start recording detected');
            setTimeout(startTimer, 100);
        }
        
        // 点击停止录音
        if (text.includes('⏹️') || text.includes('停止')) {
            console.log('[Click] Stop recording detected');
            setTimeout(stopTimer, 100);
        }
    }, true);
    
    // 页面加载时检查状态
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', checkRecordingState);
    } else {
        checkRecordingState();
    }
    
    // 每秒检查一次 localStorage 变化（备用方案）
    setInterval(function() {
        const finished = localStorage.getItem('recording_finished');
        if (finished) {
            const duration = localStorage.getItem('recording_duration');
            if (duration) {
                // 通知 Python（通过修改 URL）
                const url = new URL(window.location.href);
                url.searchParams.set('d', duration);
                url.searchParams.set('t', Date.now());
                window.history.replaceState({}, '', url);
                
                // 清理
                localStorage.removeItem('recording_finished');
            }
        }
    }, 500);
})();
</script>
""", unsafe_allow_html=True)

# ========== 标题 ==========
st.markdown('<p class="big-title">🎙️ AI语音简报助手</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">语音直接转文字，自动生成简报</p>', unsafe_allow_html=True)

# ========== 从 URL 读取录音时长 ==========
query_params = st.query_params
if 'd' in query_params:
    try:
        duration = int(query_params['d'])
        st.session_state.recording_duration = duration
        del st.query_params['d']
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
    st.caption("💡 AI简报_分享版 v2.5.0")

# ========== 工具函数 ==========
def format_duration(seconds):
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
    
    # 显示上次录音时长
    if st.session_state.recording_duration > 0:
        st.info(f"⏱️ 上次录音时长：**{format_duration(st.session_state.recording_duration)}**")
        # 显示后重置，避免重复显示
        duration_to_show = st.session_state.recording_duration
        st.session_state.recording_duration = 0
    else:
        duration_to_show = 0
    
    # 方式一：实时录音
    st.markdown("""
    <div class="info-card">
        <h4 style="margin-top: 0;">方式一：实时录音 ⏱️</h4>
        <p style="font-size: 14px; margin: 0; opacity: 0.8;">
            点击开始 → 底部显示红色计时器 → 点击停止<br>
            <strong>精确记录实际录音时间</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        from streamlit_mic_recorder import mic_recorder
        
        # 录音组件
        audio = mic_recorder(
            start_prompt="🎙️ 点击开始录音",
            stop_prompt="⏹️ 点击停止（红色计时器会显示）",
            just_once=True,
            key="mic_recorder_ios_v5"
        )
        
        # 处理录音结果
        if audio and audio.get("bytes") and not st.session_state.audio_processed:
            # 标记已处理，避免重复
            st.session_state.audio_processed = True
            
            with st.spinner("🤖 AI正在转写..."):
                result = transcribe_audio(audio["bytes"], api_key)
                
                if result["success"]:
                    st.session_state.transcribed_text = result["text"]
                    word_count = len(result["text"])
                    
                    # 显示成功信息
                    if duration_to_show > 0:
                        st.success(f"✅ 转写完成！共 {word_count} 字 | 录音时长：**{format_duration(duration_to_show)}**")
                    else:
                        st.success(f"✅ 转写完成！共 {word_count} 字")
                    
                    # 延迟重置，让用户看到结果
                    time.sleep(0.5)
                    st.session_state.audio_processed = False
                    st.rerun()
                else:
                    st.error(f"❌ 转写失败：{result['error']}")
                    st.session_state.audio_processed = False
                    
    except ImportError:
        st.error("⚠️ 录音组件加载失败，请使用方式二上传文件")
    except Exception as e:
        st.error(f"⚠️ 录音功能异常：{str(e)}")
        st.info("请尝试使用方式二上传文件")
        st.session_state.audio_processed = False
    
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
            st.session_state.recording_duration = 0
            st.session_state.audio_processed = False
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
st.caption("Made with ❤️ | 语音版v2.5.0 - iOS 录音计时器")
