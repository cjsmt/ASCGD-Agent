import os
import streamlit as st
from dotenv import load_dotenv
from agent import chat_with_model

load_dotenv(override=True)

st.set_page_config(page_title="SmartContract Security Pipeline", layout="wide")
st.title("🤖 AI 智能合约生成 & 部署平台")

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

if "first_load" not in st.session_state:
    st.session_state.first_load = True

if "processing" not in st.session_state:
    st.session_state.processing = False

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

# 现代化CSS样式 - 支持暗色模式和自适应宽度
css_path = os.path.join(os.path.dirname(__file__), "static", "styles.css")
try:
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("样式文件未找到：static/styles.css。请确保已将样式文件放到该路径。")

def get_message_width_class(content):
    """根据内容长度返回对应的宽度类别"""
    content_length = len(content)
    
    # 如果是代码块，使用长宽度
    if "```" in content or "pragma solidity" in content or "contract" in content:
        return "message-long"
    
    # 根据字符长度判断
    if content_length <= 50:
        return "message-short"
    elif content_length <= 200:
        return "message-medium"
    else:
        return "message-long"

# 主界面
st.header("💬 智能合约助手")

# 显示对话历史
chat_container = st.container()

with chat_container:
    # 如果是首次加载，显示欢迎信息
    if st.session_state.first_load and not st.session_state.messages:
        welcome_msg = """👋 你好！我是智能合约助手，我可以帮你：

• 📝 生成 Solidity 智能合约代码
• 🔍 分析和检测合约安全漏洞  
• ⚡ 优化合约逻辑和Gas消耗
• 📚 解释合约功能和实现原理
• 🚀 协助部署到区块链网络
• 📄 分析上传的合约文件

请告诉我你想要创建什么样的智能合约，或者上传合约文件让我分析！"""
        
        width_class = get_message_width_class(welcome_msg)
        
        st.markdown(
            f'<div class="assistant-message {width_class}">'
            f'<div class="message-role">🤖 智能合约助手</div>'
            f'<div class="message-content">{welcome_msg}</div>'
            f'</div>',
            unsafe_allow_html=True
        )
    
    # 显示所有历史消息
    for message in st.session_state.messages:
        if message["role"] == "user":
            # 检查是否是文件消息
            if message.get("type") == "file":
                file_info = message.get("file_info", {})
                width_class = "message-short"
                st.markdown(
                    f'<div class="user-message {width_class}">'
                    f'<div class="message-role">📎 你上传了文件</div>'
                    f'<div class="message-content">'
                    f'<strong>📄 {file_info.get("name", "文件")}</strong><br>'
                    f'<small>大小: {file_info.get("size", "未知")}</small>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                width_class = get_message_width_class(message["content"])
                st.markdown(
                    f'<div class="user-message {width_class}">'
                    f'<div class="message-role">👤 你</div>'
                    f'<div class="message-content">{message["content"]}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            # 处理代码块显示
            content = message["content"]
            width_class = get_message_width_class(content)
            
            # 简单的代码块检测和格式化
            if "```" in content:
                # 这里可以添加更复杂的代码高亮逻辑
                content = content.replace("```solidity", "<pre><code>")
                content = content.replace("```", "</code></pre>")
            
            st.markdown(
                f'<div class="assistant-message {width_class}">'
                f'<div class="message-role">🤖 智能合约助手</div>'
                f'<div class="message-content">{content}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

# 显示加载动画
if st.session_state.processing:
    st.markdown("""
    <div class="loading-overlay">
        <div class="spinner"></div>
        <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">🤖 正在处理中</div>
        <div style="font-size: 14px; opacity: 0.8;">请稍候...</div>
    </div>
    """, unsafe_allow_html=True)

# 添加一些间距
st.markdown("<div style='height: 150px;'></div>", unsafe_allow_html=True)

# 输入区域 - 固定在底部
input_container = st.container()

with input_container:
    st.markdown('<div class="input-container">', unsafe_allow_html=True)
    
    # 使用自定义的输入区域
    st.markdown('<div class="input-wrapper">', unsafe_allow_html=True)
    
    # 文本输入框
    user_input = st.text_area(
        " ",
        height=80,
        placeholder="💡 请输入你的智能合约需求，或者上传合约文件进行分析...\n例如：创建一个ERC20代币合约，或者上传.sol文件进行安全检测",
        label_visibility="collapsed",
        key="user_input",
        disabled=st.session_state.processing
    )
    
    # 自定义按钮区域
    col1, col2 = st.columns([1, 1])
    with col1:
        # 文件上传器
        uploaded_file = st.file_uploader(
            " ",
            type=['sol', 'txt', 'json', 'md'],
            label_visibility="collapsed",
            key="file_uploader",
            disabled=st.session_state.processing
        )
        
        # 处理新上传的文件
        if uploaded_file and uploaded_file not in [f["file"] for f in st.session_state.uploaded_files]:
            # 保存上传的文件信息
            file_info = {
                "name": uploaded_file.name,
                "size": f"{len(uploaded_file.getvalue()) / 1024:.1f} KB",
                "type": uploaded_file.type,
                "file": uploaded_file
            }
            st.session_state.uploaded_files.append(file_info)
            st.rerun()
    
    with col2:
        # 发送按钮
        _, _, send_col = st.columns([1, 1, 2])
        with send_col:
            send_clicked = st.button(
                "🚀 发送",
                use_container_width=True,
                type="primary",
                disabled=st.session_state.processing or (not user_input.strip() and not st.session_state.uploaded_files),
                key="send_button"
            )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # # 显示已上传的文件列表
    # if st.session_state.uploaded_files:
    #     st.markdown('<div class="file-list">', unsafe_allow_html=True)
    #     st.markdown("**已上传的文件:**")
    #     for i, file_info in enumerate(st.session_state.uploaded_files):
    #         col1, col2 = st.columns([4, 1])
    #         with col1:
    #             st.markdown(f"📄 **{file_info['name']}** ({file_info['size']})")
    #         with col2:
    #             if st.button("🗑️", key=f"remove_{i}", disabled=st.session_state.processing):
    #                 st.session_state.uploaded_files.pop(i)
    #                 st.rerun()
    #     st.markdown('</div>', unsafe_allow_html=True)
    
    # st.markdown('</div>', unsafe_allow_html=True)

    # 处理发送逻辑
    if send_clicked:
        # 构建完整的消息内容
        message_content = user_input.strip() if user_input.strip() else ""
        
        # 如果有上传的文件，添加到消息中
        file_names = []
        if st.session_state.uploaded_files:
            file_names = [f["name"] for f in st.session_state.uploaded_files]
            file_paths = [f["file"].name for f in st.session_state.uploaded_files]
            st.info(f"文件路径: {', '.join(file_paths)}")
            
            if message_content:
                # 如果既有文本又有文件，创建一个组合消息
                message_content += f"\n\n📎 上传的文件: {', '.join(file_names)}"
            else:
                # 如果只有文件，创建一个文件分析请求
                message_content = f"📎 请分析这些文件: {', '.join(file_names)}"
        
        if message_content:
            # 只添加一条用户消息到历史
            st.session_state.messages.append({
                "role": "user", 
                "content": message_content,
                "files": st.session_state.uploaded_files.copy()  # 保存文件信息供后台使用
            })
            st.session_state.first_load = False
            st.session_state.processing = True
            
            # 清空输入和文件
            st.session_state.uploaded_files = []
            
            # 立即重新运行以显示加载状态
            st.rerun()

# 处理AI回复（在重新运行后执行）
if st.session_state.processing and st.session_state.messages:
    # 获取最后一条用户消息
    last_user_message = [m for m in st.session_state.messages if m["role"] == "user"][-1]
    
    # 获取AI回复
    try:
        # 构建完整的请求内容，包含文件信息
        request_content = last_user_message["content"]
        
        # 如果有文件，将文件内容也传递给后台
        if "files" in last_user_message and last_user_message["files"]:
            # 这里可以添加文件内容读取逻辑
            file_info_text = "\n\n上传的文件内容："
            for file_info in last_user_message["files"]:
                uploaded_file = file_info["file"]
                # 读取文件内容
                file_content = uploaded_file.getvalue().decode('utf-8')
                file_info_text += f"\n\n--- {file_info['name']} ---\n{file_content}"
            
            request_content += file_info_text
        
        response = chat_with_model(request_content)
        assistant_response = response.content if hasattr(response, 'content') else str(response)
        
        # 添加助手消息到历史
        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
        
    except Exception as e:
        error_message = f"❌ 处理时出现错误：{str(e)}"
        st.session_state.messages.append({"role": "assistant", "content": error_message})
    
    # 完成处理
    st.session_state.processing = False
    st.rerun()

# 侧边栏控制
with st.sidebar:
    st.header("⚙️ 设置")
    
    if st.button("🗑️ 清空对话历史", use_container_width=True, disabled=st.session_state.processing):
        st.session_state.messages = []
        st.session_state.uploaded_files = []
        st.session_state.first_load = True
        st.rerun()
    
    st.markdown("---")
    st.subheader("📁 支持的文件类型")
    st.markdown("""
    - `.sol` - Solidity 合约文件
    - `.txt` - 文本文件
    - `.json` - 配置文件
    - `.md` - 文档文件
    """)
    
    st.markdown("---")
    st.subheader("💡 使用提示")
    st.markdown("""
    - 💬 用自然语言描述合约需求
    - 📝 上传文件进行安全分析
    - 🔧 生成特定标准合约
    - ⚡ 优化Gas消耗
    - 🚀 协助部署到区块链
    - ⚠️ 代码请务必审计后再部署
    """)
    
    # 显示对话统计
    if st.session_state.messages:
        user_count = len([m for m in st.session_state.messages if m["role"] == "user"])
        assistant_count = len([m for m in st.session_state.messages if m["role"] == "assistant"])
        file_count = len([m for m in st.session_state.messages if m.get("files")])
        
        st.markdown("---")
        st.subheader("📊 对话统计")
        st.write(f"用户消息: {user_count}")
        st.write(f"包含文件的对话: {file_count}")
        st.write(f"助手回复: {assistant_count}")