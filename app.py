# AI简报小助手 - 语音版v2.1.0 (Cloud Ready)
# 部署到 Streamlit Cloud 的版本

import streamlit as st
from openai import OpenAI
import os
import tempfile
import io

# ========== 页面设置 ==========
st.set_page_config(page_title="AI语音简报助手", page_icon="🎙️")

# 自定义样式
st.markdown("""
<style>
.big-title { font-size: 42px; font-weight: bold; color: #FF6B6B; text-align: center; }
.subtitle { font-size: 18px; color: #666; text-align: center; margin-bottom: 30px; }
.voice-box { background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 5px solid #FF6B6B; margin: 10px 0; }
.stButton>button { border-radius: 20px; height: 3em; font-weight: bold; width: 100%; }
</style>
""", unsafe_allow_html=True)

# ========== 标题 ==========
st.markdown('<p class="big-title">🎙️ AI语音简报助手</p>', unsafe_allow_html=True)
st.markdown('<p class="subtitle">语音直接转文字，自动生成简报</p>', unsafe_allow_html=True)

# ========== 侧边栏设置 ==========
with st.sidebar:
    st.header("⚙️ 设置")
    
    # 关键修改：从环境变量或secrets读取API密钥（Cloud安全要求）
    api_key = st.text_input("🔑 硅基流动 API密钥", 
                           value=st.secrets.get("SILICONFLOW_API_KEY", ""),
                           type="password",
                           help="在 siliconflow.cn 免费获取")
    
    if not api_key:
        st.warning("⚠️ 请先输入API密钥")
        st.markdown("""
        **获取步骤：**
        1. 访问 [siliconflow.cn](https://siliconflow.cn)
        2. 手机号注册（送14元）
        3. 创建API密钥
        4. 复制到左侧输入框
        """)
    else:
        st.success("✅ 密钥已配置")

# ========== 语音转文字函数 ==========
def transcribe_audio(audio_bytes, api_key):
    """使用硅基流动Whisper API转文字"""
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
if not api_key:
    st.info("👈 请先在左侧边栏输入API密钥")
else:
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("🎤 语音输入")
        
        # 方式一：实时录音
        st.markdown("""
        <div class="voice-box">
            <h4>方式一：实时录音转文字</h4>
            <p style="color: #666; font-size: 14px;">点击录音，说完后自动转写并填入右侧</p>
        </div>
        """, unsafe_allow_html=True)
        
        try:
            from streamlit_mic_recorder import mic_recorder
            
            audio = mic_recorder(
                start_prompt="🎙️ 点击开始录音",
                stop_prompt="⏹️ 点击停止并转写",
                just_once=True,
                key="mic_recorder"
            )
            
            if audio and audio["bytes"]:
                with st.spinner("🤖 AI正在转写..."):
                    result = transcribe_audio(audio["bytes"], api_key)
                    
                    if result["success"]:
                        st.session_state.transcribed_text = result["text"]
                        st.success(f"✅ 转写完成！共 {len(result['text'])} 字")
                        st.rerun()
                    else:
                        st.error(f"❌ 转写失败：{result['error']}")
                        
        except ImportError:
            st.warning("⚠️ 录音组件加载中...")
            st.info("如果长时间无法加载，请刷新页面")
        
        st.divider()
        
        # 方式二：上传录音文件
        st.subheader("📁 方式二：上传录音（自动转文字）")
        
        audio_file = st.file_uploader(
            "上传录音文件（mp3/wav/m4a）", 
            type=['mp3', 'wav', 'm4a', 'webm'],
            help="上传后自动转为文字，无需手动输入"
        )
        
        if audio_file:
            st.audio(audio_file, format=f'audio/{audio_file.type.split("/")[1]}')
            
            if st.button("🎯 开始语音转文字", type="primary", key="transcribe"):
                with st.spinner("🤖 AI正在识别语音，请稍候..."):
                    result = transcribe_audio(audio_file.getvalue(), api_key)
                    
                    if result["success"]:
                        st.session_state.transcribed_text = result["text"]
                        st.success(f"✅ 识别完成！共 {len(result['text'])} 个字符")
                        st.markdown("**识别结果预览：**")
                        st.info(result["text"][:200] + "..." if len(result["text"]) > 200 else result["text"])
                        st.rerun()
                    else:
                        st.error(f"❌ 识别失败：{result['error']}")
                        st.info("提示：请检查API密钥是否正确，或网络连接是否正常")
    
    with col2:
        st.subheader("📝 编辑与生成")
        
        briefing_type = st.selectbox(
            "选择简报类型",
            ["工作日报", "会议纪要", "学习笔记", "新闻摘要"],
            key="briefing_type"
        )
        
        default_text = st.session_state.get("transcribed_text", "")
        
        content = st.text_area(
            "编辑内容（可修改AI识别的文字）",
            value=default_text,
            height=300,
            placeholder="在这里编辑...可以手动输入、粘贴，或从左侧语音导入"
        )
        
        if content != st.session_state.get("transcribed_text", ""):
            st.session_state.transcribed_text = content
        
        custom_req = st.text_input("特殊要求（可选）", placeholder="例如：重点突出数据，用表格展示")
        
        col_gen, col_clear = st.columns([3, 1])
        with col_gen:
            if st.button("✨ 生成简报", type="primary", use_container_width=True):
                if not content.strip():
                    st.error("❌ 内容不能为空！请先语音输入或手动填写")
                else:
                    with st.spinner("🤖 AI正在整理成简报..."):
                        try:
                            client = OpenAI(
                                api_key=api_key,
                                base_url="https://api.siliconflow.cn/v1"
                            )
                            
                            prompts = {
                                "工作日报": "将以下内容整理成工作日报，包含：1今天完成的工作 2遇到的问题 3明天的计划",
                                "会议纪要": "将以下内容整理成会议纪要，包含：1会议主题 2讨论要点 3决议事项 4待办任务",
                                "学习笔记": "将以下内容整理成结构化学习笔记，包含：1核心概念 2重点内容 3个人思考",
                                "新闻摘要": "将以下内容整理成新闻摘要，包含：1核心事件 2关键数据 3影响分析"
                            }
                            
                            system_prompt = prompts[briefing_type]
                            if custom_req:
                                system_prompt += f"。额外要求：{custom_req}"
                            
                            response = client.chat.completions.create(
                                model="deepseek-ai/DeepSeek-V3",
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": content}
                                ],
                                temperature=0.7,
                                max_tokens=2000
                            )
                            
                            result = response.choices[0].message.content
                            st.session_state.generated_result = result
                            
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
            st.success("✅ 简报生成完成！")
            st.markdown(st.session_state.generated_result)
            st.download_button(
                "📋 下载简报",
                st.session_state.generated_result,
                file_name=f"简报_{briefing_type}_{os.path.basename(tempfile.mktemp())[:6]}.txt",
                mime="text/plain"
            )

st.divider()
st.caption("Made with ❤️ | 语音版v2.1.0 - Cloud Ready")