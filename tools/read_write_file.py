import re
import os
import streamlit as st
from langchain.tools import tool

def extract_solidity_from_response(resp):
    """从 LLM 响应文本中提取 Solidity 代码（模块级可复用）。

    支持：```solidity ...```, ```...```, ~~~ 代码块，或从关键字（pragma/contract）截取。
    返回提取后的代码字符串（若无则返回原始文本的清理版本）。
    """
    if isinstance(resp, dict):
        text = resp.get('output') or resp.get('text') or str(resp)
    else:
        text = str(resp)

    code_blocks = []
    patterns = [r"```(?:solidity)?\s*\n(.*?)```", r"~~~(?:solidity)?\s*\n(.*?)~~~", r"```(.*?)```"]
    for p in patterns:
        for m in re.findall(p, text, flags=re.S | re.I):
            if isinstance(m, tuple):
                m = m[0]
            code_blocks.append(m.strip())

    if code_blocks:
        return max(code_blocks, key=len)

    keywords = ["pragma solidity", "contract ", "interface ", "library "]
    lower = text.lower()
    indices = [lower.find(k) for k in keywords if lower.find(k) != -1]
    if indices:
        start = min(indices)
        return text[start:].strip()

    return text.strip()

@tool("write_file", description=(
    "Write Solidity source to a file named {contract_name}.sol under the project's contracts/ directory. "
    "The provided content may include markdown code fences or plain text; the tool will extract the Solidity code if present. "
    "Returns the written file path on success or an error message on failure."
))
def write_file(contract_name: str, content: str) -> str:
    base_dir = os.path.dirname(os.path.dirname(__file__))
    contract_dir = os.path.join(base_dir, "contracts")
    file_path = os.path.join(contract_dir, f"{contract_name}.sol")
    os.makedirs(contract_dir, exist_ok=True)
    
    code = extract_solidity_from_response(content)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        msg = f"合约已生成：{file_path}"
        try:
            st.success(msg)
        except Exception:
            # streamlit may not be available in some runtime contexts
            pass
        return file_path
    except Exception as e:
        err = f"写入文件失败: {e}"
        try:
            st.error(err)
        except Exception:
            pass
        return err
    

@tool("read_file", description=(
    "Read the content of a file at the specified path {contract_path}. "
    "Returns the smart contract code in the file as a string or an error message if reading fails."
))
def read_file(contract_path: str) -> str:
    """读取指定路径的文件内容，返回字符串或错误信息。"""
    try:
        with open(contract_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        return extract_solidity_from_response(content)
    except Exception as e:
        err = f"读取文件失败: {e}"
        try:
            st.error(err)
        except Exception:
            pass
        return err