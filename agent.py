import os
import streamlit as st
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langgraph.prebuilt import create_react_agent
from tools.deploy_tool import deploy_solidity_contract
from tools.read_write_file import write_file, read_file

from dotenv import load_dotenv
load_dotenv(override=True)

DeepSeek_API_KEY = os.environ.get("DEEPSEEK_API_KEY")
llm = init_chat_model("deepseek-chat", model_provider="deepseek")


def build_agent():
    system_prompt = "你是Solidity智能合约生成器，请根据用户需求生成符合ERC20/ERC721等标准的Solidity代码，你可以使用工具进行一键上链部署智能合约"

    tools = [deploy_solidity_contract, write_file, read_file]
    # agent = create_tool_calling_agent(llm, tool, prompt)
    memory = MemorySaver()
    # agent_executor = AgentExecutor(agent=agent, tools=tool, verbose=True)
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