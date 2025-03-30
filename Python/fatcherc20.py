# from web3 import Web3
#
# # Connect to Ethereum node (Infura example)
# web3 = Web3(Web3.HTTPProvider("https://mainnet.infura.io/v3/YOUR_API_KEY"))
#
# # ERC20 token contract
# contract_address = Web3.to_checksum_address("0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48")  # USDC
# abi = [{
#     "anonymous": False,
#     "inputs": [
#         {"indexed": True, "name": "from", "type": "address"},
#         {"indexed": True, "name": "to", "type": "address"},
#         {"indexed": False, "name": "value", "type": "uint256"}
#     ],
#     "name": "Transfer",
#     "type": "event"
# }]
#
# contract = web3.eth.contract(address=contract_address, abi=abi)
#
# latest = web3.eth.block_number
#
# # Get transfers in the last 100 blocks
# events = contract.events.Transfer().get_logs(fromBlock=latest - 100, toBlock=latest)
# for e in events:
#     print(f"{e['args']['from']} -> {e['args']['to']} : {e['args']['value']}")
#

# Simulated Transfer event logs (dummy data)
dummy_logs = [
    {
        "args": {
            "from": "0xAbC123...0001",
            "to": "0xDeF456...0002",
            "value": 1000
        }
    },
    {
        "args": {
            "from": "0xAbC123...0003",
            "to": "0xDeF456...0004",
            "value": 500
        }
    },
    {
        "args": {
            "from": "0xAbC123...0001",
            "to": "0xDeF456...0002",
            "value": 200
        }
    }
]

# Simulate event processing
def parse_transfer_events(logs):
    print("Transfer Event Logs:")
    for log in logs:
        from_addr = log["args"]["from"]
        to_addr = log["args"]["to"]
        value = log["args"]["value"]

        print(f"{from_addr} -> {to_addr} : {value} tokens")

# Run it
parse_transfer_events(dummy_logs)