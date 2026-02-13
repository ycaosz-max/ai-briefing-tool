# AI简报小助手 - 语音版v2.1.1 (iOS 修复版)
# 修复：iPhone 上 API 密钥输入框无响应问题

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

# 关键修复：iOS Safari 兼容样式
st.markdown("""
<style>
/* iOS 基础修复 */
* {
    -webkit-tap-highlight-color: transparent;
    -webkit-touch-callout: none;
}

/* 输入框 iOS 修复 */
.stTextInput input, .stTextArea textarea {
    -webkit-appearance: none !important;
    -webkit-user-select: text !important;
    user-select: text !important;
    font-size: 16px !important; /* iOS 小于16px会缩放 */
    touch-action: manipulation;
}

/* 按钮 iOS 修复 */
.stButton button {
    -webkit-appearance: none;
    touch-action: manipulation;
}

/* 移动端适配 */
@media (max-width: 768px) {
    .big-title { font-size: 24px !important; }
    .subtitle { font-size: 14px !important; }
    .main .block-container { padding: 1rem; }
}
</style>
""", unsafe_allow_html=True)

# ========== 标题 ==========
st.markdown('<p class="big-title">🎙️ AI语音简报助手</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">语音直接转文字，自动生成简报</p>', unsafe_allow_html=True)

# ========== 关键修复：将API输入移到主界面，避免侧边栏点击问题 ==========

# 先检查是否有API密钥（环境变量或之前输入）
api_key = st.session_state.get("api_key", "")

if not api_key:
    # 主界面显示API输入（不在侧边栏）
    st.warning("⚠️ 首次使用需要输入 API 密钥")
    
    with st.expander("🔑 点击此处输入 API 密钥", expanded=True):
        st.markdown("""
        **获取步骤：**
        1. 访问 [硅基流动](https://cloud.siliconflow.cn/i/nZqCjymq)
        2. 注册并完成实名认证
        3. 创建您的API 密钥
        4. 复制到下方输入框
        """)
        
        # 关键修复：使用 st.text_area 代替 st.text_input，iOS 兼容性更好
        # 或者用 st.text_input 但添加 key 和 on_change
        api_input = st.text_input(
            "API 密钥",
            value="",
            type="password",
            placeholder="sk-xxxxxxxxxxxxxxxx",
            key="api_key_input",
            help="密钥以 sk- 开头"
        )
        
        # iOS 修复：添加明确的确认按钮
        if st.button("✅ 确认并保存", type="primary", key="save_api_key"):
            if api_input and api_input.startswith("sk-"):
                st.session_state.api_key = api_input
                st.success("✅ API 密钥已保存！")
                st.rerun()
            else:
                st.error("❌ 请输入正确的 API 密钥（以 sk- 开头）")
    
    st.stop()  # 没有密钥时不显示后续内容

# ========== 侧边栏（简化版，避免iOS问题） ==========
with st.sidebar:
    st.header("⚙️ 设置")
    st.success("✅ API 已配置")
    
    if st.button("🔄 更换 API 密钥"):
        del st.session_state.api_key
        st.rerun()
    
    st.divider()
    st.caption("💡 AI简报_分享版")

# ========== 语音转文字函数 ==========
def transcribe_audio(audio_bytes, api_key):
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
        
        os.unlink(tmp_path)
        return {"success": True, "text": transcription}
        
    except Exception as e:
        return {"success": False, "error": str(e)}

# ========== 主界面 ==========
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🎤 语音输入")
    
    # 方式一：实时录音
    st.markdown("""
    <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
        <h4>方式一：实时录音转文字</h4>
        <p style="color: #666; font-size: 14px; margin: 0;">
            📱 iPhone 提示：请使用 Safari 浏览器<br>
            点击录音 → 说话 → 自动转写填入右侧
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        from streamlit_mic_recorder import mic_recorder
        
        # iOS 修复：添加帮助提示
        audio = mic_recorder(
            start_prompt="🎙️ 点击开始录音",
            stop_prompt="⏹️ 点击停止",
            just_once=True,
            key="mic_recorder_ios"
        )
        
        if audio and audio.get("bytes"):
            with st.spinner("🤖 AI正在转写..."):
                result = transcribe_audio(audio["bytes"], api_key)
                
                if result["success"]:
                    st.session_state.transcribed_text = result["text"]
                    st.success(f"✅ 转写完成！共 {len(result['text'])} 字")
                    st.rerun()
                else:
                    st.error(f"❌ 转写失败：{result['error']}")
                    
    except ImportError:
        st.error("⚠️ 录音组件加载失败")
    
    st.divider()
    
    # 方式二：上传录音（iOS 更可靠的方式）
    st.subheader("📁 方式二：上传录音")
    
    # iOS 提示
    st.info("""
    💡 **iPhone 用户推荐此方式**：
    1. 用"语音备忘录"录好音
    2. 点击分享 → 存储到"文件"
    3. 在这里选择文件上传
    """)
    
    audio_file = st.file_uploader(
        "选择录音文件", 
        type=['mp3', 'wav', 'm4a', 'webm'],
        help="支持 mp3, wav, m4a 格式"
    )
    
    if audio_file:
        st.audio(audio_file, format=f'audio/{audio_file.type.split("/")[1]}')
        
        if st.button("🎯 开始转写", type="primary"):
            with st.spinner("🤖 正在识别..."):
                result = transcribe_audio(audio_file.getvalue(), api_key)
                
                if result["success"]:
                    st.session_state.transcribed_text = result["text"]
                    st.success(f"✅ 完成！共 {len(result['text'])} 字")
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
        placeholder="语音转写内容会出现在这里..."
    )
    
    if content != st.session_state.get("transcribed_text", ""):
        st.session_state.transcribed_text = content
    
    custom_req = st.text_input("特殊要求", placeholder="例如：重点突出数据")
    
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
        st.download_button(
            "📋 下载",
            st.session_state.generated_result,
            file_name=f"简报_{briefing_type}.txt"
        )

st.divider()
st.caption("Made with ❤️ | 语音版v2.1.1 - iOS 优化版")
