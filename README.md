# ASCGD-Agent

A lightweight AI-driven platform for generating, analyzing, and deploying smart contracts with a single click (based on Streamlit + LangGraph/LangChain). This repository contains tools for generating, reading, and writing Solidity contracts, as well as scripts for compiling and deploying contracts to Ethereum-compatible nodes.

## Project Structure (Core Files/Directories)

- [app.py](app.py) — Streamlit Web UI entry point
- [agent.py](agent.py) — Agent construction and external session interface ([`agent.build_agent`](agent.py) / [`agent.chat_with_model`](agent.py))
- [test.py](test.py) — Local quick deployment example (calls [`tools.deploy_tool.deploy_solidity_contract`](tools/deploy_tool.py))
- [requirements.txt](requirements.txt) — Python dependencies
- [package.json](package.json) — Root directory NPM configuration (depends on OpenZeppelin)
- [.gitignore](.gitignore)
- [static/styles.css](static/styles.css) — Web UI styles
- [contracts/](contracts/) — Solidity contract directory (this directory is ignored in .gitignore and will be written to at runtime)
- [hardhat/](hardhat/) — Hardhat example project
- tools/
  - [tools/deploy_tool.py](tools/deploy_tool.py) — Main tool for compiling and deploying contracts ([`tools.deploy_tool.deploy_solidity_contract`](tools/deploy_tool.py))
  - [tools/read_write_file.py](tools/read_write_file.py) — Tool for writing/reading Solidity files ([`tools.read_write_file.write_file`](tools/read_write_file.py), [`tools.read_write_file.read_file`](tools/read_write_file.py))
  - [tools/solidity_vulnerability_tool.py](tools/solidity_vulnerability_tool.py) — Tool for performing security checks on Solidity contracts ([`tools.solidity_vulnerability_tool.security_check_solidity`](tools/solidity_vulnerability_tool.py), [`tools.solidity_vulnerability_tool.analyze_with_slither`](tools/solidity_vulnerability_tool.py))

## Quick Start

1. Clone the repository and navigate to the directory (already in workspace).
2. Create and activate a Python virtual environment (optional).
3. Install Python dependencies:

```sh
pip install -r requirements.txt
```

4. Install and initialize the Node.js environment (only for MacOS, for Windows please refer to GPT for instructions, download Node version v22.x.x):

```sh
# 1. Install nvm (if you haven't installed it yet)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.6/install.sh | bash
# After installation, restart the terminal or execute:
export NVM_DIR="$([ -z "${XDG_CONFIG_HOME-}" ] && printf %s "${HOME}/.nvm" || printf %s "${XDG_CONFIG_HOME}/nvm")"
[ -s "$NVM_DIR/nvm.sh" ] && \. "$NVM_DIR/nvm.sh"

# 2. Install Node version 20
nvm install 20

# 3. Use this version
nvm use 20

# 4. Confirm version
node -v
npm -v
```

5. Navigate to the Hardhat example and install dependencies:

```sh
# 1. Create and navigate to the project directory
mkdir hardhat
cd hardhat

# 2. Initialize npm project
npm init -y 

# 3. Open package.json and add "type": "module" within {}
{
  "name": "mytoken-hardhat",
  "version": "1.0.0",
  "type": "module",
  "scripts": {},
  "devDependencies": {}
}

# 4. Install Hardhat
npm install --save-dev hardhat

# 5. Initialize Hardhat project
npx hardhat --init

# 6. Start Hardhat node
npx hardhat node
```

6. Configure environment variables:

- Use a `.env` file to set third-party LLM API keys, such as `DEEPSEEK_API_KEY`, which the project loads automatically via `dotenv`:
  - Read in [`agent.py`](agent.py): `os.environ.get("DEEPSEEK_API_KEY")`

7. Run the Web UI (Streamlit):

```sh
streamlit run app.py
```

Open your browser to access the local address (Streamlit will print the URL) and interact with the smart contract assistant, upload `.sol` files, or request contract generation and deployment.

## Local Quick Deployment Example

The repository provides [test.py](test.py) as a local example. It calls the tool function:

- [`tools.deploy_tool.deploy_solidity_contract`](tools/deploy_tool.py)

Example run:

```sh
# Before running, please comment out the @tool on line 125 in tools/deploy_tool.py
python test.py
```

Please ensure:

- A local Ethereum-compatible RPC node (such as Hardhat, Anvil, or Ganache) is running and `rpc_url` points to the correct address.
- A test private key is used in `test.py` (the example private key is for local testing only).

## Tool Descriptions

- Contract Read/Write
  - [`tools.read_write_file.write_file`](tools/read_write_file.py): Writes Solidity code returned by LLM or any text to `contracts/{contract_name}.sol`.
  - [`tools.read_write_file.read_file`](tools/read_write_file.py): Reads a specified file and attempts to extract Solidity source code.
- Compilation and Deployment
  - [`tools.deploy_tool.deploy_solidity_contract`](tools/deploy_tool.py):
    - Automatically collects locally relative import source files (`collect_sources`), installs/sets up solc using `py-solc-x`, calls `compile_standard` to compile, and deploys the contract to the specified RPC via `web3`.
    - Supports automatic selection of solc version based on `pragma solidity` in the contract; if not found, it will fallback to `0.8.19`.
    - Outputs a JSON string containing deployment results (`contractAddress`, `txHash`, `abi`, `receipt`) or error messages.
- Security Analysis
  - [`tools.solidity_vulnerability_tool.security_check_solidity`](tools/solidity_vulnerability_tool.py): Performs a basic security scan on Solidity contracts, checking for common vulnerabilities such as reentrancy, integer overflow, and access control issues.
  - [`tools.solidity_vulnerability_tool.analyze_with_slither`](tools/solidity_vulnerability_tool.py): Runs Slither static analysis on the provided Solidity code, returning a detailed report of potential issues and recommendations.

## Usage Recommendations and Precautions

- Security: Do not expose or use real private keys in production environments. The example private keys in this project are for local testing only.
- Dependencies:
  - `solc` (binary) must be installed or allow `py-solc-x` to download the specified version.
- .gitignore: By default, `contracts/` and `mytoken-hardhat/` are ignored to prevent generated files from being committed to the repository.
- UI Interaction: [`app.py`](app.py) concatenates the uploaded file content and passes it to the Agent ([`agent.chat_with_model`](agent.py)), which uses [`tools.*` tools] for file reading/writing, compilation, deployment, or security checks.

## Common Commands

- Run the UI:

```sh
streamlit run app.py
```

- Run the example deployment:

```sh
python test.py
```

- Run tests in the Hardhat example (navigate to mytoken-hardhat):

```sh
cd mytoken-hardhat
npx hardhat test
```

## Code Location (Quick Reference)

- Agent and Sessions: [`agent.py`](agent.py) ([`agent.build_agent`](agent.py), [`agent.chat_with_model`](agent.py))
- Web UI: [`app.py`](app.py)
- Deployment Tool: [`tools/deploy_tool.py`](tools/deploy_tool.py) ([`tools.deploy_tool.deploy_solidity_contract`](tools/deploy_tool.py))
- Read/Write Tool: [`tools/read_write_file.py`](tools/read_write_file.py) ([`tools.read_write_file.write_file`](tools/read_write_file.py), [`tools.read_write_file.read_file`](tools/read_write_file.py))
- Security Tool: [`tools/solidity_vulnerability_tool.py`](tools/solidity_vulnerability_tool.py) ([`tools.solidity_vulnerability_tool.security_check_solidity`](tools/solidity_vulnerability_tool.py), [`tools.solidity_vulnerability_tool.analyze_with_slither`](tools/solidity_vulnerability_tool.py))
- Styles: [`static/styles.css`](static/styles.css)

## License & Contributions

- This repository currently does not specify a license. If you plan to open source or share, please add a LICENSE file.
- Contributions are welcome! Please submit issues or PRs to improve deployment processes, contract templates, or security detection logic.