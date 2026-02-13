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
if 'recording_start_time' not in st.session_state:
    st.session_state.recording_start_time = None
if 'recording_duration' not in st.session_state:
    st.session_state.recording_duration = 0

# ========== CSS + JavaScript 实时计时器 ==========
st.markdown("""
<style>
:root {
    --bg-primary: #ffffff;
    --bg-secondary: #f0f2f6;
    --text-primary: #1f1f1f;
    --text-secondary: #666666;
    --accent-color: #ff4b4b;
    --timer-bg: rgba(255, 75, 75, 0.95);
    --timer-text: #ffffff;
}

@media (prefers-color-scheme: dark) {
    :root {
        --bg-primary: #000000;
        --bg-secondary: #1c1c1e;
        --text-primary: #ffffff;
        --text-secondary: #8e8e93;
        --accent-color: #0a84ff;
        --timer-bg: rgba(10, 132, 255, 0.95);
    }
    .stApp { background-color: #000000 !important; }
}

* {
    -webkit-tap-highlight-color: transparent;
    -webkit-touch-callout: none;
}

.stApp {
    background-color: var(--bg-primary);
    color: var(--text-primary);
}

/* 录音计时器 - 屏幕中央浮动 */
.recording-overlay {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: rgba(0, 0, 0, 0.7);
    z-index: 999998;
    display: none;
    justify-content: center;
    align-items: center;
    backdrop-filter: blur(5px);
}

.recording-overlay.active {
    display: flex;
}

.recording-timer-box {
    background: var(--timer-bg);
    color: var(--timer-text);
    padding: 40px 60px;
    border-radius: 24px;
    text-align: center;
    box-shadow: 0 20px 60px rgba(0,0,0,0.4);
    animation: pulse 2s infinite;
    min-width: 200px;
}

.recording-timer-box .timer-icon {
    font-size: 48px;
    margin-bottom: 10px;
}

.recording-timer-box .timer-display {
    font-size: 64px;
    font-weight: bold;
    font-family: -apple-system-monospace, monospace;
    font-variant-numeric: tabular-nums;
    letter-spacing: 4px;
    line-height: 1;
}

.recording-timer-box .timer-label {
    font-size: 16px;
    margin-top: 15px;
    opacity: 0.9;
    text-transform: uppercase;
    letter-spacing: 3px;
}

.recording-timer-box .timer-sub {
    font-size: 13px;
    margin-top: 8px;
    opacity: 0.7;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.02); }
}

/* 停止按钮提示 */
.stop-hint {
    position: fixed;
    bottom: 100px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(255, 255, 255, 0.2);
    color: white;
    padding: 12px 24px;
    border-radius: 20px;
    font-size: 14px;
    z-index: 999999;
    display: none;
}

.recording-overlay.active + .stop-hint,
.stop-hint.active {
    display: block;
}

/* 响应式 */
@media (max-width: 768px) {
    .recording-timer-box {
        padding: 30px 40px;
        margin: 20px;
    }
    .recording-timer-box .timer-display {
        font-size: 48px;
    }
    .recording-timer-box .timer-icon {
        font-size: 36px;
    }
}

/* 其他样式 */
.stButton button {
    -webkit-appearance: none;
    border-radius: 10px;
    background-color: var(--accent-color) !important;
    color: white !important;
    font-weight: 600;
}

.big-title {
    font-size: 32px;
    font-weight: bold;
    color: var(--text-primary);
}

.subtitle {
    font-size: 16px;
    color: var(--text-secondary);
}
</style>

<!-- 录音计时器 UI -->
<div id="recording-overlay" class="recording-overlay">
    <div class="recording-timer-box">
        <div class="timer-icon">🔴</div>
        <div class="timer-display" id="timer-display">00:00</div>
        <div class="timer-label">正在录音</div>
        <div class="timer-sub">点击停止按钮结束</div>
    </div>
</div>

<div id="stop-hint" class="stop-hint">👇 点击下方停止按钮结束录音</div>

<script>
(function() {
    let timerInterval = null;
    let startTime = null;
    let isRecording = false;
    
    function formatTime(seconds) {
        const mins = Math.floor(seconds / 60).toString().padStart(2, '0');
        const secs = (seconds % 60).toString().padStart(2, '0');
        return mins + ':' + secs;
    }
    
    function startTimer() {
        if (isRecording) return;
        isRecording = true;
        startTime = Date.now();
        
        document.getElementById('recording-overlay').classList.add('active');
        document.getElementById('stop-hint').classList.add('active');
        
        const display = document.getElementById('timer-display');
        display.textContent = '00:00';
        
        // 立即更新一次，然后每秒更新
        timerInterval = setInterval(function() {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            display.textContent = formatTime(elapsed);
        }, 100);
        
        console.log('🎙️ 录音开始，时间戳:', startTime);
    }
    
    function stopTimer() {
        if (!isRecording) return;
        isRecording = false;
        
        clearInterval(timerInterval);
        
        const duration = Math.floor((Date.now() - startTime) / 1000);
        const durationMs = Date.now() - startTime; // 精确到毫秒
        
        // 保存到 localStorage，页面刷新后也能获取
        localStorage.setItem('recording_duration', duration);
        localStorage.setItem('recording_duration_ms', durationMs);
        localStorage.setItem('recording_stop_time', Date.now());
        
        // 隐藏计时器
        document.getElementById('recording-overlay').classList.remove('active');
        document.getElementById('stop-hint').classList.remove('active');
        
        console.log('⏹️ 录音停止，时长:', duration, '秒');
        
        // 显示完成提示
        showCompletion(duration);
        
        return duration;
    }
    
    function showCompletion(seconds) {
        const div = document.createElement('div');
        div.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #30d158;
            color: white;
            padding: 30px 50px;
            border-radius: 20px;
            font-size: 24px;
            font-weight: bold;
            z-index: 1000000;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            animation: popIn 0.3s ease;
        `;
        div.innerHTML = `
            <div style="font-size: 48px; margin-bottom: 10px;">✅</div>
            <div>录音完成</div>
            <div style="font-size: 32px; margin-top: 10px;">${formatTime(seconds)}</div>
        `;
        document.body.appendChild(div);
        
        setTimeout(() => {
            div.style.opacity = '0';
            div.style.transition = 'opacity 0.5s';
            setTimeout(() => div.remove(), 500);
        }, 2000);
    }
    
    // 监听按钮变化
    function watchButtons() {
        const checkInterval = setInterval(function() {
            const buttons = document.querySelectorAll('button');
            
            buttons.forEach(function(btn) {
                const text = btn.textContent || '';
                
                // 检测开始按钮变成停止按钮（表示录音中）
                if ((text.includes('⏹️') || text.includes('停止')) && !btn._recordingWatched) {
                    btn._recordingWatched = true;
                    
                    // 开始计时
                    if (!isRecording) {
                        startTimer();
                    }
                    
                    // 绑定点击事件
                    btn.addEventListener('click', function() {
                        setTimeout(function() {
                            if (isRecording) {
                                const duration = stopTimer();
                                // 设置 URL 参数，让 Python 能读取
                                const url = new URL(window.location);
                                url.searchParams.set('recording_duration', duration);
                                url.searchParams.set('t', Date.now());
                                window.history.replaceState({}, '', url);
                            }
                        }, 100);
                    });
                }
                
                // 如果按钮变回开始状态，重置标记
                if (text.includes('🎙️') && btn._recordingWatched && !isRecording) {
                    btn._recordingWatched = false;
                }
            });
        }, 200);
    }
    
    // 添加动画
    const style = document.createElement('style');
    style.textContent = `
        @keyframes popIn {
            from { transform: translate(-50%, -50%) scale(0.8); opacity: 0; }
            to { transform: translate(-50%, -50%) scale(1); opacity: 1; }
        }
    `;
    document.head.appendChild(style);
    
    // 启动监听
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', watchButtons);
    } else {
        watchButtons();
    }
})();
</script>
""", unsafe_allow_html=True)

# ========== 标题 ==========
st.markdown('<p class="big-title">🎙️ AI语音简报助手</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">语音直接转文字，自动生成简报</p>', unsafe_allow_html=True)

# ========== 从 URL 参数读取录音时长 ==========
query_params = st.query_params
if 'recording_duration' in query_params:
    try:
        st.session_state.recording_duration = int(query_params['recording_duration'])
        # 清除参数，避免重复读取
        del st.query_params['recording_duration']
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
    st.caption("💡 AI简报_分享版 v2.4.0")

# ========== 工具函数 ==========
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
    
    # 显示上次录音时长
    if st.session_state.recording_duration > 0:
        st.info(f"⏱️ 上次录音时长：**{format_duration(st.session_state.recording_duration)}**")
    
    # 方式一：实时录音
    st.markdown("""
    <div style="padding: 15px; border-radius: 12px; margin: 10px 0; 
                background-color: var(--bg-secondary); 
                border: 1px solid var(--border-color);">
        <h4 style="margin-top: 0; color: var(--text-primary);">方式一：实时录音 ⏱️</h4>
        <p style="color: var(--text-secondary); font-size: 14px; margin: 0;">
            点击开始 → 屏幕显示计时器 → 点击停止自动转写<br>
            <strong>精确记录实际录音时间</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        from streamlit_mic_recorder import mic_recorder
        
        audio = mic_recorder(
            start_prompt="🎙️ 点击开始录音",
            stop_prompt="⏹️ 点击停止",
            just_once=True,
            key="mic_recorder_timer_v1"
        )
        
        # 检查是否有新的录音时长数据（从 JavaScript 通过 URL 传递）
        current_duration = st.session_state.get('recording_duration', 0)
        
        if audio and audio.get("bytes"):
            # 使用 JavaScript 记录的时长，如果没有则使用 session state 中的
            duration = current_duration
            
            with st.spinner(f"🤖 AI正在转写..."):
                result = transcribe_audio(audio["bytes"], api_key)
                
                if result["success"]:
                    st.session_state.transcribed_text = result["text"]
                    word_count = len(result["text"])
                    
                    # 显示成功信息（包含字数和精确时长）
                    success_msg = f"✅ 转写完成！共 {word_count} 字"
                    if duration > 0:
                        success_msg += f" | 录音时长：**{format_duration(duration)}**"
                    
                    st.success(success_msg)
                    
                    # 重置时长记录
                    st.session_state.recording_duration = 0
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
st.caption("Made with ❤️ | 语音版v2.4.0 - 精确录音计时")
