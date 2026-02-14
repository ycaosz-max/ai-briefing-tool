import streamlit as st
from openai import OpenAI
import os
import tempfile
import base64

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

@media (max-width: 768px) {
    .big-title { font-size: 26px !important; }
    .subtitle { font-size: 14px !important; }
    .main .block-container { padding: 1rem; }
    .stApp { padding-bottom: env(safe-area-inset-bottom); }
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
            # 使用 verbose_json 格式获取详细结果
            transcription = client.audio.transcriptions.create(
                model="FunAudioLLM/SenseVoiceSmall",
                file=audio,
                response_format="verbose_json"  # 改为 verbose_json 获取结构化数据
            )
            
            # 调试：打印原始响应类型和内容
            print(f"Transcription type: {type(transcription)}")
            print(f"Transcription value: {transcription}")
            
            # 处理不同的返回格式
            result_text = ""
            
            # 如果是对象，尝试获取 text 属性
            if hasattr(transcription, 'text'):
                result_text = transcription.text
            # 如果是字典
            elif isinstance(transcription, dict):
                result_text = transcription.get('text', '')
            # 如果是字符串（可能包含 "text" 前缀）
            elif isinstance(transcription, str):
                result_text = transcription
                # 去除可能的 "text=" 前缀
                if result_text.startswith('text='):
                    result_text = result_text[5:]
            else:
                # 尝试转换为字符串
                result_text = str(transcription)
                # 去除常见的包装字符
                result_text = result_text.strip("'\"")
                if result_text.startswith('text='):
                    result_text = result_text[5:]
            
            # 最终清理：确保不是 "text" 这个单词本身
            if result_text.strip().lower() == 'text':
                result_text = ""
            
            return {"success": True, "text": result_text}
            
    except Exception as e:
        return {"success": False, "error": str(e), "text": ""}
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.unlink(tmp_path)

# ========== iOS 优化下载组件 ==========
def ios_friendly_download(content, filename, briefing_type):
    b64 = base64.b64encode(content.encode('utf-8')).decode()
    unique_id = f"{briefing_type}_{abs(hash(content)) % 10000}"
    
    html = f"""
    <script>
    function download_{unique_id}() {{
        const link = document.createElement('a');
        link.href = "data:text/plain;charset=utf-8;base64,{b64}";
        link.download = "{filename}";
        link.style.display = 'none';
        document.body.appendChild(link);
        link.click();
        setTimeout(() => {{
            document.body.removeChild(link);
        }}, 100);
        showToast("📥 文件已下载");
    }}
    
    function copy_{unique_id}() {{
        const text = atob("{b64}");
        navigator.clipboard.writeText(text).then(() => {{
            showToast("📋 内容已复制到剪贴板");
        }}).catch(err => {{
            const textarea = document.createElement('textarea');
            textarea.value = text;
            document.body.appendChild(textarea);
            textarea.select();
            document.execCommand('copy');
            document.body.removeChild(textarea);
            showToast("📋 内容已复制");
        }});
    }}
    
    function showToast(message) {{
        const oldToast = document.getElementById('ios-toast');
        if (oldToast) oldToast.remove();
        
        const toast = document.createElement('div');
        toast.id = 'ios-toast';
        toast.style.cssText = `
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #30d158;
            color: white;
            padding: 20px 30px;
            border-radius: 16px;
            font-size: 16px;
            font-weight: 600;
            z-index: 999999;
            text-align: center;
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
            animation: fadeIn 0.3s ease;
            min-width: 200px;
        `;
        toast.innerHTML = `
            <div style="font-size: 40px; margin-bottom: 8px;">✓</div>
            <div>${{message}}</div>
        `;
        document.body.appendChild(toast);
        
        setTimeout(() => {{
            toast.style.opacity = '0';
            toast.style.transition = 'opacity 0.5s';
            setTimeout(() => toast.remove(), 500);
        }}, 2500);
    }}
    </script>
    
    <style>
    @keyframes fadeIn {{
        from {{ opacity: 0; transform: translate(-50%, -50%) scale(0.9); }}
        to {{ opacity: 1; transform: translate(-50%, -50%) scale(1); }}
    }}
    
    .ios-btn-group {{
        display: flex;
        gap: 10px;
        margin-top: 15px;
    }}
    
    .ios-btn {{
        flex: 1;
        padding: 12px 20px;
        border-radius: 12px;
        font-size: 15px;
        font-weight: 600;
        cursor: pointer;
        border: none;
        transition: all 0.2s;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    
    .ios-btn-primary {{
        background-color: var(--accent-color, #0a84ff);
        color: white;
    }}
    
    .ios-btn-secondary {{
        background-color: var(--bg-card, #f0f2f6);
        color: var(--accent-color, #0a84ff);
        border: 2px solid var(--accent-color, #0a84ff);
    }}
    
    .ios-btn:active {{
        transform: scale(0.95);
        opacity: 0.8;
    }}
    
    .ios-tip {{
        margin-top: 12px;
        padding: 12px;
        background: var(--bg-secondary, #f0f2f6);
        border-radius: 10px;
        font-size: 13px;
        color: var(--text-secondary, #666);
        line-height: 1.5;
    }}
    </style>
    
    <div class="ios-btn-group">
        <button class="ios-btn ios-btn-primary" onclick="download_{unique_id}()">
            ⬇️ 下载文件
        </button>
        <button class="ios-btn ios-btn-secondary" onclick="copy_{unique_id}()">
            📋 复制内容
        </button>
    </div>
    
    <div class="ios-tip">
        💡 <strong>iOS 提示：</strong><br>
        • 下载的文件可在"文件"App 或浏览器下载记录中找到<br>
        • 如果下载未开始，请使用"复制内容"粘贴到备忘录保存
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)

# ========== 主界面 ==========
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎤 语音输入")
    
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
            with st.spinner("🤖 AI正在转写..."):
                result = transcribe_audio(audio["bytes"], api_key)
                
                if result["success"]:
                    # 清理后的文本
                    clean_text = result["text"]
                    
                    # 额外检查：如果文本就是 "text" 或为空，显示警告
                    if not clean_text or clean_text.strip().lower() in ['text', '']:
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
                    clean_text = result["text"]
                    if not clean_text or clean_text.strip().lower() in ['text', '']:
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
                        client = OpenAI(api_key=api_key, base_url="https://api.siliconflow.cn/v1")
                        
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
        
        ios_friendly_download(
            st.session_state.generated_result,
            f"简报_{briefing_type}.txt",
            briefing_type
        )

st.divider()
st.caption("Made with ❤️ | 语音版v2.2.2 - 修复 text 显示问题")
