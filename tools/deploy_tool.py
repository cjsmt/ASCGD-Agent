# tools/deploy_tool.py
import os
import re
import json
import time
from typing import List, Optional, Dict
from langchain.tools import tool
from solcx import install_solc, set_solc_version, compile_standard
from web3 import Web3
from web3.exceptions import TransactionNotFound
from web3.datastructures import AttributeDict
from hexbytes import HexBytes

def convert(obj):
    if isinstance(obj, HexBytes):
        return obj.hex()
    if isinstance(obj, AttributeDict):
        return {k: convert(v) for k, v in obj.items()}
    if isinstance(obj, dict):
        return {k: convert(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [convert(v) for v in obj]
    return obj


PRAGMA_REGEX = re.compile(r'pragma\s+solidity\s+([^;]+);')

IMPORT_REGEX = re.compile(r'^\s*import\s+["\'](.+?)["\'];', re.MULTILINE)

def find_pragma_version(source: str) -> Optional[str]:
    """
    从源文件中提取 pragma solidity 声明，尝试返回显式版本号（如 0.8.19）。
    如果只带 ^ 或 >= 范围，尝试提取第一个出现的显式版本号（含小数点）。
    否则返回 None。
    """
    m = PRAGMA_REGEX.search(source)
    if not m:
        return None
    pragma = m.group(1).strip()
    # 常见形式: ^0.8.19, >=0.8.0 <0.9.0, 0.8.19
    # 尝试找到显式 x.y.z
    v_match = re.search(r'(\d+\.\d+\.\d+)', pragma)
    if v_match:
        return v_match.group(1)
    # 退化：找 x.y
    v_match2 = re.search(r'(\d+\.\d+)', pragma)
    if v_match2:
        return v_match2.group(1)
    return None

def collect_sources(entry_path: str, base_path: Optional[str] = None, visited: Optional[Dict[str,str]] = None) -> Dict[str, Dict[str,str]]:
    """
    递归收集 entry_path 及其相对导入的源文件内容，返回符合 solc compile_standard 的 sources 字典:
    { "path/Relative.sol": {"content": "..."}, ... }
    仅解析相对路径(import "Foo.sol"; 或 "./lib/Bar.sol")。对于以 @ 开头或 node_modules 引用，尝试按相对路径查找，但不会联网。
    """
    if visited is None:
        visited = {}
    if base_path is None:
        base_path = os.path.dirname(os.path.abspath(entry_path))

    def _resolve(import_path: str, current_dir: str) -> Optional[str]:
        # 处理 @openzeppelin 等外部依赖
        if import_path.startswith('@'):
            # 查找 node_modules
            node_modules_path = os.path.normpath(os.path.join(base_path, 'node_modules', import_path))
            print(node_modules_path)
            if os.path.exists(node_modules_path):
                return os.path.abspath(node_modules_path)
            # 也可以尝试在当前目录的 node_modules 中查找
            node_modules_path2 = os.path.normpath(os.path.join(current_dir, 'node_modules', import_path))
            if os.path.exists(node_modules_path2):
                return os.path.abspath(node_modules_path2)
        # 绝对路径或相对路径
        if os.path.isabs(import_path):
            if os.path.exists(import_path):
                return os.path.abspath(import_path)
            return None
        # 先试 current_dir/import_path
        candidate = os.path.normpath(os.path.join(current_dir, import_path))
        if os.path.exists(candidate):
            return os.path.abspath(candidate)
        # 再试 base_path/import_path
        candidate2 = os.path.normpath(os.path.join(base_path, import_path))
        if os.path.exists(candidate2):
            return os.path.abspath(candidate2)
        # 不能解析（例如 @openzeppelin/...） -> 跳过
        return None

    def _collect(path: str):
        path = os.path.abspath(path)
        if path in visited:
            return
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        visited[path] = content
        # parse imports
        for m in IMPORT_REGEX.finditer(content):
            imp = m.group(1)
            resolved = _resolve(imp, os.path.dirname(path))
            if resolved:
                _collect(resolved)
            else:
                # 如果无法解析，跳过并保留原 import（编译可能因为缺失依赖失败）
                # 也可以尝试查找 in-project node_modules，但这里不做网络/包管理操作
                pass

    _collect(entry_path)
    # convert visited to solc sources mapping with file-relative keys
    sources = {}
    for path, content in visited.items():
        # key use relative path from project root (base_path) if possible to keep output readable
        try:
            rel = os.path.relpath(path, start=base_path)
        except Exception:
            rel = os.path.basename(path)
        # solc accepts paths; use rel as key
        sources[rel] = {"content": content}
    return sources

# -----------------------
# Main Tool
# -----------------------

@tool
def deploy_solidity_contract(
    sol_path: str,
    contract_name: str,
    rpc_url: str,
    private_key: str,
    constructor_args: Optional[List] = None,
    gas: Optional[int] = None,
    timeout: int = 600
) -> str:
    """
    编译并部署 Solidity 合约（适用于测试网）。
    参数:
      - sol_path: 本地 .sol 文件路径（入口文件）
      - contract_name: 要部署的合约名称（文件中定义的 contract 名称）
      - rpc_url: 节点 RPC HTTP URL
      - private_key: 部署者私钥（测试网专用）
      - constructor_args: 可选列表，传给 constructor 的参数
      - gas: 可选显式 gas 限制；若为 None 则会尝试估算
      - timeout: 等待交易上链的超时时间（秒）
    返回:
      - JSON 字符串，包含 status, contractAddress, txHash, abi, rawReceipt 或 error 信息
    注意:
      - 只解析并包含本地可解析到的 import 文件；对于 @openzeppelin/... 等外部依赖，需要提前将库放在本地或使用完整路径。
      - 该工具会安装 solc（根据 pragma 选择版本或使用默认），需要联网以下载 solc 二进制。
    """

    # 基础检查
    if not os.path.exists(sol_path):
        return json.dumps({"status": "error", "error": f"sol file not found: {sol_path}"}, ensure_ascii=False)

    # try:
    # 读取入口文件内容以检测 pragma
    with open(sol_path, 'r', encoding='utf-8') as f:
        entry_src = f.read()

    # 尝试提取 pragma 指定的具体版本（优先）
    pragma_ver = find_pragma_version(entry_src)
    if pragma_ver:
        solc_version = pragma_ver
    else:
        # 默认回退版本（可根据需要修改）
        solc_version = "0.8.19"

    # 安装并设置 solc
    try:
        install_solc(solc_version)
        set_solc_version(solc_version)
    except Exception as e:
        # 如果安装指定版本失败，尝试回退到 0.8.19
        fallback = "0.8.19"
        if solc_version != fallback:
            try:
                install_solc(fallback)
                set_solc_version(fallback)
                solc_version = fallback
            except Exception as e2:
                return json.dumps({"status": "error", "error": f"install_solc failed: {e}; fallback failed: {e2}"}, ensure_ascii=False)
        else:
            return json.dumps({"status": "error", "error": f"install_solc failed: {e}"}, ensure_ascii=False)

    # 收集 sources（递归本地 imports）
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(sol_path)))
    sources = collect_sources(sol_path, base_dir)

    # 构造 compile_standard 的 input
    compile_input = {
        "language": "Solidity",
        "sources": sources,
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "evm.bytecode", "evm.deployedBytecode", "devdoc", "userdoc"]
                }
            }
        }
    }

    compiled = compile_standard(compile_input, allow_paths=base_dir)
    # compiled structure: compiled["contracts"][file_key][ContractName]

    # Search for contract_name across sources
    found = None
    for file_key, contracts in compiled.get("contracts", {}).items():
        if contract_name in contracts:
            found = (file_key, contracts[contract_name])
            break

    if not found:
        # try fallback: sometimes contract_name may be prefixed by path like 'path:Name' in older outputs
        return json.dumps({"status": "error", "error": f"Contract '{contract_name}' not found in compiled output. Available contracts: {list(sum([list(c.keys()) for c in compiled.get('contracts', {}).values()], []))}"}, ensure_ascii=False)

    file_key, contract_meta = found
    abi = contract_meta.get("abi")
    bytecode = contract_meta.get("evm", {}).get("bytecode", {}).get("object")
    if not bytecode or bytecode == "0x" or bytecode == "":
        return json.dumps({"status": "error", "error": "Compiled bytecode is empty. Possibly abstract contract or missing implementation."}, ensure_ascii=False)

    # Setup web3
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    if not web3.is_connected():
        return json.dumps({"status": "error", "error": f"Cannot connect to RPC: {rpc_url}"}, ensure_ascii=False)

    account = web3.eth.account.from_key(private_key)
    sender = account.address

    # Prepare contract and transaction
    Contract = web3.eth.contract(abi=abi, bytecode=bytecode)
    constructor_args = constructor_args or []

    # Build transaction dict (without gas for now)
    nonce = web3.eth.get_transaction_count(sender)
    tx_dict = Contract.constructor(*constructor_args).build_transaction({
        "from": sender,
        "nonce": nonce,
        "gas": gas or 3_000_000,
        # gas/gasPrice/chainId/value will be set/estimated below
    })

    # Ensure chainId present
    try:
        chain_id = web3.eth.chain_id
        tx_dict["chainId"] = chain_id
    except Exception:
        # ignore if unavailable
        pass

    # 判断节点是否支持 EIP-1559 动态费交易
    try:
        # 取当前推荐的 maxPriorityFeePerGas
        max_priority_fee = web3.eth.max_priority_fee
        tx_dict["maxPriorityFeePerGas"] = max_priority_fee
        # 设置 maxFeePerGas，略高于 gasPrice
        tx_dict["maxFeePerGas"] = web3.eth.gas_price + max_priority_fee
        # 删除 legacy gasPrice 避免报错
        if "gasPrice" in tx_dict:
            del tx_dict["gasPrice"]
    except Exception:
        # 如果不支持动态费，回退 legacy gasPrice
        tx_dict["gasPrice"] = web3.eth.gas_price

    # Sign and send
    signed = account.sign_transaction(tx_dict)
    raw = signed.raw_transaction
    tx_hash = web3.eth.send_raw_transaction(raw)

    # 等待回执
    start = time.time()
    receipt = None
    while True:
        try:
            receipt = web3.eth.get_transaction_receipt(tx_hash)
            if receipt:
                break
        except TransactionNotFound:
            pass
        except Exception:
            # 某些节点不支持 get_transaction_receipt 轮询方式，使用 wait_for_transaction_receipt
            try:
                receipt = web3.eth.wait_for_transaction_receipt(tx_hash, timeout=timeout)
                break
            except Exception as e:
                return json.dumps({"status": "error", "error": f"waiting receipt error: {e}"}, ensure_ascii=False)
        if time.time() - start > timeout:
            return json.dumps({"status": "error", "error": f"timeout waiting for transaction receipt (tx: {tx_hash.hex()})"}, ensure_ascii=False)
        time.sleep(3)

    # 成功
    result = {
        "status": "success",
        "contractAddress": receipt.contractAddress,
        "txHash": tx_hash.hex(),
        "chainId": web3.eth.chain_id if hasattr(web3.eth, "chain_id") else None,
        "abi": abi,
        "receipt": dict(receipt),
    }

    result = convert(result)

    return json.dumps(result, ensure_ascii=False)

    # except Exception as e:
    #     return json.dumps({"status": "error", "error": str(e)}, ensure_ascii=False)
