import os
import streamlit as st
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from tools.deploy_tool import deploy_solidity_contract
from tools.read_write_file import write_file, read_file
from tools.solidity_vulnerability_tool import security_check_solidity, analyze_with_slither
# from langchain_community.llms import Ollama
# from langchain_experimental.llms.ollama_functions import OllamaFunctions

from dotenv import load_dotenv
load_dotenv(override=True)

DeepSeek_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
llm = init_chat_model("deepseek-chat", model_provider="deepseek")
# llm = OllamaFunctions(model="llama3.2", base_url="http://localhost:11434")


def build_agent():
    system_prompt = """You are a Solidity smart contract generation expert. Follow this workflow strictly:

[Phase 1: Code Generation]
1. Analyze the user's requirements and generate a complete Solidity smart contract.
2. Explain the contract's functionality and features in detail.
3. After presenting the code, proactively offer the following next steps:

Choose a follow-up action:
🔍 [Security Check] - Check the code for security vulnerabilities
📊 [Deep Analysis] - Run static analysis via Slither
💾 [Save File] - Save the code to a .sol file
🚀 [Deploy Contract] - Deploy to a blockchain network
➡️ [Continue Optimization] - Modify code based on feedback

[Tool Usage Rules]
- Only call the security tools when the user explicitly requests "security check" or similar.
- Do not run security analysis automatically after generating code; ask the user first.
- Ensure the final output language matches the user's input language."""

    tools = [deploy_solidity_contract, write_file, read_file, security_check_solidity, analyze_with_slither]
    memory = MemorySaver()
    agent_executor = create_react_agent(llm, tools, checkpointer=memory, prompt=system_prompt)
    return agent_executor

smart_contract_agent = build_agent()

def chat_with_model(user_prompt: str, conversation_id=None):
    # 使用对话ID作为线程ID，确保每个对话有独立记忆
    thread_id = conversation_id if conversation_id else "default"
    config = {"configurable": {"thread_id": thread_id}}
    
    final_response = None
    for chunk in smart_contract_agent.stream({"messages": [user_prompt]}, config, stream_mode="values"):
        last_message = chunk["messages"][-1]
        last_message.pretty_print()
        final_response = chunk
    return final_response["messages"][-1] if final_response else None