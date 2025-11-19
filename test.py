from tools.deploy_tool import deploy_solidity_contract

constructor_args = [1_000_000 * 10**18]

result = deploy_solidity_contract(
    sol_path="./contracts/MyToken.sol",
    contract_name="MyToken",
    rpc_url="http://127.0.0.1:8545/",
    private_key="0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80",
    constructor_args=constructor_args,
    gas=2_000_000

)

print(result)