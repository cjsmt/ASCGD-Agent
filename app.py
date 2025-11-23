import os
import streamlit as st
from dotenv import load_dotenv
from agent import chat_with_model
import datetime

load_dotenv(override=True)

st.set_page_config(page_title="SmartContract Security Pipeline", layout="wide")
st.title("🤖 AI Smart Contract Generation & Deployment Platform")

# 初始化对话历史
if "messages" not in st.session_state:
    st.session_state.messages = []

if "first_load" not in st.session_state:
    st.session_state.first_load = True

if "processing" not in st.session_state:
    st.session_state.processing = False

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

if "conversations" not in st.session_state:
    st.session_state.conversations = []

if "current_conversation" not in st.session_state:
    st.session_state.current_conversation = None

# 现代化CSS样式 - 支持暗色模式和自适应宽度
css_path = os.path.join(os.path.dirname(__file__), "static", "styles.css")
try:
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
except FileNotFoundError:
    st.warning("Stylesheet not found: static/styles.css. Please ensure the file exists at that path.")

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
st.header("💬 Smart Contract Assistant")

# 显示对话历史
chat_container = st.container()

with chat_container:
    # 如果是首次加载，显示欢迎信息
    if st.session_state.first_load and not st.session_state.messages:
        welcome_msg = """👋 Hello! I'm your Smart Contract Assistant. I can help you with:

• 📝 Generate Solidity smart contract code (ERC20/ERC721 etc.)

• 🔍 Analyze and detect security vulnerabilities

• ⚡ Optimize contract logic and gas usage

• 📚 Explain contract functionality and implementation details

• 🚀 Assist with deployment to blockchain networks

• 📄 Analyze uploaded contract files

Tell me what kind of smart contract you'd like to create, or upload a .sol file for analysis!"""
        
        width_class = get_message_width_class(welcome_msg)
        
        st.markdown(
            f'<div class="assistant-message {width_class}">'
            f'<div class="message-role">🤖 Smart Contract Assistant</div>'
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
                    f'<div class="message-role">📎 You uploaded a file</div>'
                    f'<div class="message-content">'
                    f'<strong>📄 {file_info.get("name", "file")}</strong><br>'
                    f'<small>Size: {file_info.get("size", "unknown")}</small>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            else:
                width_class = get_message_width_class(message["content"])
                st.markdown(
                    f'<div class="user-message {width_class}">'
                    f'<div class="message-role">👤 You</div>'
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
                f'<div class="message-role">🤖 Smart Contract Assistant</div>'
                f'<div class="message-content">{content}</div>'
                f'</div>',
                unsafe_allow_html=True
            )

# 显示加载动画
if st.session_state.processing:
    st.markdown("""
    <div class="loading-overlay">
        <div class="spinner"></div>
        <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">🤖 Processing</div>
        <div style="font-size: 14px; opacity: 0.8;">Please wait...</div>
    </div>
    """, unsafe_allow_html=True)

# 添加一些间距
st.markdown("<div style='height: 180px;'></div>", unsafe_allow_html=True)

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
        placeholder="💡 Describe your smart contract requirement or upload a contract file for analysis...\nE.g.: Create an ERC20 token, or upload a .sol file for security review",
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
                "🚀 Send",
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
            
            if message_content:
                message_content += f"\n\n📎 Uploaded files: {', '.join(file_names)}"
            else:
                message_content = f"📎 Please analyze these files: {', '.join(file_names)}"
        
        if message_content:
            # 如果是新对话且没有保存过，创建新对话记录
            if st.session_state.current_conversation is None and st.session_state.messages:
                # 使用第一条用户消息作为标题
                title = message_content[:30] + "..." if len(message_content) > 30 else message_content
                new_conv = {
                    "title": title,
                    "messages": st.session_state.messages.copy() + [{"role": "user", "content": message_content}],
                    "created_at": datetime.datetime.now().isoformat()
                }
                st.session_state.conversations.append(new_conv)
                st.session_state.current_conversation = len(st.session_state.conversations) - 1
            
            # 添加用户消息到历史
            st.session_state.messages.append({
                "role": "user", 
                "content": message_content,
                "files": st.session_state.uploaded_files.copy()
            })
            
            # 如果是已有对话，更新对话记录
            if st.session_state.current_conversation is not None:
                st.session_state.conversations[st.session_state.current_conversation]["messages"] = st.session_state.messages.copy()
            
            st.session_state.first_load = False
            st.session_state.processing = True
            st.session_state.uploaded_files = []
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
            file_info_text = "\n\nUploaded file contents:"
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
        error_message = f"❌ Error occurred during processing: {str(e)}"
        st.session_state.messages.append({"role": "assistant", "content": error_message})

    # 添加助手消息到历史后，更新对话记录
    if st.session_state.current_conversation is not None:
        st.session_state.conversations[st.session_state.current_conversation]["messages"] = st.session_state.messages.copy()
    
    # 完成处理
    st.session_state.processing = False
    st.rerun()

# 侧边栏控制（替换原有的侧边栏内容）
with st.sidebar:
    st.header("⚙️ Conversations")
    
    # 新建对话按钮（位于顶部）
    if st.button("+ New Chat", use_container_width=True, key="new_chat_btn", disabled=st.session_state.processing):
        # 保存当前对话到会话列表（如果有内容）
        if st.session_state.messages:
            # 使用第一条用户消息作为对话标题
            first_user_msg = next((msg for msg in st.session_state.messages if msg["role"] == "user"), None)
            if first_user_msg:
                title = first_user_msg["content"][:30] + "..." if len(first_user_msg["content"]) > 30 else first_user_msg["content"]
            else:
                title = f"对话 {len(st.session_state.conversations) + 1}"
            
            st.session_state.conversations.append({
                "title": title,
                "messages": st.session_state.messages.copy(),
                "created_at": datetime.datetime.now().isoformat()
            })
        
        # 清空当前对话，开启新会话
        st.session_state.messages = []
        st.session_state.uploaded_files = []
        st.session_state.first_load = True
        st.session_state.current_conversation = None
        st.rerun()

    st.markdown("---")
    st.subheader("Conversation History")
    
    if not st.session_state.conversations:
        st.info("No conversation history yet. Click '+ New Chat' or start typing.")
    else:
        # 显示所有对话历史（最新的在最上面）
        for idx, conv in enumerate(reversed(st.session_state.conversations)):
            actual_idx = len(st.session_state.conversations) - 1 - idx
            
            cols = st.columns([3, 1])
            with cols[0]:
                # 显示对话标题和选中状态
                is_current = st.session_state.current_conversation == actual_idx
                btn_label = f"● {conv['title']}" if is_current else conv['title']
                
                if st.button(btn_label, key=f"conv_{actual_idx}", use_container_width=True, 
                           disabled=st.session_state.processing):
                    # 加载选中的对话
                    st.session_state.messages = conv["messages"].copy()
                    st.session_state.first_load = False
                    st.session_state.current_conversation = actual_idx
                    st.rerun()
            
            with cols[1]:
                if st.button("🗑️", key=f"del_{actual_idx}", disabled=st.session_state.processing):
                    # 删除对话
                    st.session_state.conversations.pop(actual_idx)
                    # 如果删除的是当前对话，清空当前消息
                    if st.session_state.current_conversation == actual_idx:
                        st.session_state.messages = []
                        st.session_state.current_conversation = None
                        st.session_state.first_load = True
                    st.rerun()

    st.markdown("---")
    
    # 全局清空按钮
    if st.button("🧹 Clear All Conversations", use_container_width=True, disabled=st.session_state.processing):
        st.session_state.messages = []
        st.session_state.uploaded_files = []
        st.session_state.first_load = True
        st.session_state.conversations = []
        st.session_state.current_conversation = None
        st.rerun()
    
    st.markdown("---")
    st.subheader("💡 Tips")
    st.markdown("""
    - 💬 Describe your contract requirements in natural language
    - 📝 Upload files for security analysis
    - 🔧 Generate contracts following specific standards
    - ⚡ Optimize gas usage
    - 🚀 Help deploy to blockchain networks
    - ⚠️ Always audit generated code before deploying
    """)