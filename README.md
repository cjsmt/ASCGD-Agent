# ASCGD-Agent

轻量级的 AI 驱动智能合约生成、分析与一键部署平台（基于 Streamlit + LangGraph/LangChain）。本仓库包含用于生成/读取/写入 Solidity 合约的工具以及将编译并部署合约到以太坊兼容节点的脚本。

## 项目结构（核心文件/目录）

- [app.py](app.py) — Streamlit Web UI 入口
- [agent.py](agent.py) — Agent 构建与对外会话接口（[`agent.build_agent`](agent.py) / [`agent.chat_with_model`](agent.py)）
- [test.py](test.py) — 本地快速部署示例（调用 [`tools.deploy_tool.deploy_solidity_contract`](tools/deploy_tool.py)）
- [requirements.txt](requirements.txt) — Python 依赖
- [package.json](package.json) — 根目录 NPM 配置（依赖 OpenZeppelin）
- [.gitignore](.gitignore)
- [static/styles.css](static/styles.css) — Web UI 样式
- [contracts/](contracts/) — Solidity 合约目录（此目录在 .gitignore 中被忽略，运行时会写入）
- [hardhat/](hardhat/) — Hardhat 示例工程
- tools/
  - [tools/deploy_tool.py](tools/deploy_tool.py) — 编译并部署合约的主工具（[`tools.deploy_tool.deploy_solidity_contract`](tools/deploy_tool.py)）
  - [tools/read_write_file.py](tools/read_write_file.py) — 写入/读取 Solidity 文件工具（[`tools.read_write_file.write_file`](tools/read_write_file.py)，[`tools.read_write_file.read_file`](tools/read_write_file.py)）

## 快速开始

1. 克隆仓库并进入目录（已在 workspace 中）
2. 创建并激活 Python 虚拟环境（可选）
3. 安装 Python 依赖：

```sh
pip install -r requirements.txt
```

4. 安装并初始化node.js环境（仅展示MacOS系统，Windows系统这一步可自行GPT，要下载node版本为v22.x.x）

```sh
# 1. 安装 nvm（如果你还没有安装）
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.6/install.sh | bash
# 安装完成后，重启终端或执行：
export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 2. 安装22版本的node
nvm install 20

# 3. 使用这个版本
nvm use 20

# 4. 确认版本
node -v
npm -v
```

5. 进入 Hardhat 示例并安装依赖

```sh
# 1. 创建并进入项目目录
mkdir hardhat
cd hardhat

# 2. 初始化npm项目
npm init -y 


# 3. 打开 package.json，在 {} 内添加 "type": "module"，示例：
{
  "name": "mytoken-hardhat",
  "version": "1.0.0",
  "type": "module",
  "scripts": {},
  "devDependencies": {}
}

# 4. 安装Hardhat
npm install --save-dev hardhat

# 5. 初始化Hardhat项目
npx hardhat --init

# 6. 启动Hardhat节点
npx hardhat node
```

6. 配置环境变量

- 使用 `.env` 文件设置第三方 LLM API key，例如 `DEEPSEEK_API_KEY`，项目通过 `dotenv` 自动加载：
  - 在 [`agent.py`](agent.py) 中读取：`os.environ.get("DEEPSEEK_API_KEY")`

7. 运行 Web UI（Streamlit）

```sh
streamlit run app.py
```

打开浏览器访问本地地址（Streamlit 会打印 URL），通过 UI 与智能合约助手交互、上传 `.sol` 文件或请求生成合约并一键部署。

## 本地快速部署示例

仓库提供了 [test.py](test.py) 作为本地示例。它调用了工具函数：

- [`tools.deploy_tool.deploy_solidity_contract`](tools/deploy_tool.py)

示例运行：

```sh
# 运行前，请先把tools/deploy_tool.py文件里125行的@tool给注释掉
python test.py
```

请确保：

- 本地运行着以太坊兼容 RPC 节点（如 Hardhat、Anvil 或 Ganache）并将 `rpc_url` 指向正确地址；
- 在 `test.py` 中使用的是测试私钥（示例私钥仅用于本地测试）。

## 工具说明

- 合约读写
  - [`tools.read_write_file.write_file`](tools/read_write_file.py)：将 LLM 返回或任意文本提取 Solidity 代码并写入 `contracts/{contract_name}.sol`。
  - [`tools.read_write_file.read_file`](tools/read_write_file.py)：读取指定文件并尝试提取 Solidity 源码。
- 编译与部署
  - [`tools.deploy_tool.deploy_solidity_contract`](tools/deploy_tool.py)：
    - 自动收集本地相对 import 的源文件（`collect_sources`），使用 `py-solc-x` 安装/设置 solc，调用 `compile_standard` 编译，并通过 `web3` 将合约部署到指定 RPC。
    - 支持根据合约内 `pragma solidity` 自动选取 solc 版本，若找不到会 fallback 到 `0.8.19`。
    - 输出为 JSON 字符串，包含部署结果（`contractAddress`、`txHash`、`abi`、`receipt`）或错误信息。

## 使用建议与注意事项

- 安全性：不要在生产环境暴露或使用真实私钥。本项目示例私钥仅用于本地测试。
- 依赖项：
  - 需要安装 `solc`（二进制）或允许 `py-solc-x` 下载指定版本；
- .gitignore: 默认忽略了 `contracts/` 和 `mytoken-hardhat/` 等以避免将生成文件提交到仓库。
- UI 交互：[`app.py`](app.py) 将上传文件内容拼接后传给 Agent（[`agent.chat_with_model`](agent.py)），Agent 使用 [`tools.*` 工具] 做文件读写、编译部署或安全检测。

## 常见命令

- 运行 UI：

```sh
streamlit run app.py
```

- 运行示例部署：

```sh
python test.py
```

- 在 Hardhat 示例中运行测试（进入 mytoken-hardhat）：

```sh
cd mytoken-hardhat
npx hardhat test
```

## 代码定位（快速参考）

- Agent 与会话：[`agent.py`](agent.py)（[`agent.build_agent`](agent.py), [`agent.chat_with_model`](agent.py)）
- Web UI：[`app.py`](app.py)
- 部署工具：[`tools/deploy_tool.py`](tools/deploy_tool.py)（[`tools.deploy_tool.deploy_solidity_contract`](tools/deploy_tool.py)）
- 读写工具：[`tools/read_write_file.py`](tools/read_write_file.py)（[`tools.read_write_file.write_file`](tools/read_write_file.py), 
- 样式：[`static/styles.css`](static/styles.css)

## 许可证 & 贡献

- 本仓库目前未指定许可证。若准备开源或共享，请补充 LICENSE 文件。
- 欢迎提交 issue 或 PR 来改进部署流程、合约模板或安全检测逻辑。