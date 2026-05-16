from web3 import Web3
from app.core.config import settings

NETWORKS = {
    "ethereum": {
        "rpc_url": settings.ETH_RPC_URL,
        "symbol": "ETH",
    },
    "bsc": {
        "rpc_url": settings.BSC_RPC_URL,
        "symbol": "BNB",
    },
    "polygon": {
        "rpc_url": settings.POLYGON_RPC_URL,
        "symbol": "MATIC",
    },
}

TOKENS = {
    "polygon": {
        "usdt": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "usdc": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "dai": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
    },
    "ethereum": {
        "usdt": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "usdc": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "dai": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
    },
    "bsc": {
        "usdt": "0x55d398326f99059fF775485246999027B3197955",
        "usdc": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
        "dai": "0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3",
    },
}

ERC20_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "symbol",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
    {
        "constant": True,
        "inputs": [],
        "name": "name",
        "outputs": [{"name": "", "type": "string"}],
        "type": "function",
    },
]

def get_web3(network: str) -> Web3:
    network = network.lower()
    network_data = NETWORKS.get(network)

    if not network_data:
        raise ValueError("Red no soportada")

    rpc_url = network_data.get("rpc_url")

    if not rpc_url:
        raise ValueError("RPC URL no configurada")

    web3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))

    try:
        connected = web3.is_connected()
    except Exception as error:
        raise ConnectionError(f"No se pudo conectar al RPC: {error}")

    if not connected:
        raise ConnectionError(f"No se pudo conectar a la red blockchain usando RPC: {rpc_url}")

    return web3

def is_valid_address(address: str) -> bool:
    return Web3.is_address(address)

def get_native_balance(address: str, network: str = "ethereum"):
    network = network.lower()

    if not is_valid_address(address):
        raise ValueError("Dirección wallet inválida")

    web3 = get_web3(network)
    checksum_address = Web3.to_checksum_address(address)

    balance_wei = web3.eth.get_balance(checksum_address)
    balance = web3.from_wei(balance_wei, "ether")

    symbol = NETWORKS[network]["symbol"]

    return {
        "type": "native",
        "network": network,
        "address": checksum_address,
        "balance": float(balance),
        "symbol": symbol,
    }

def get_token_contract_address(network: str, token: str):
    network = network.lower()
    token = token.lower()

    network_tokens = TOKENS.get(network)

    if not network_tokens:
        raise ValueError("No hay tokens configurados para esta red")

    contract_address = network_tokens.get(token)

    if not contract_address:
        raise ValueError("Token no soportado en esta red")

    return contract_address

def get_erc20_balance(address: str, token: str, network: str = "polygon"):
    network = network.lower()
    token = token.lower()

    if not is_valid_address(address):
        raise ValueError("Dirección wallet inválida")

    web3 = get_web3(network)

    wallet_address = Web3.to_checksum_address(address)
    contract_address = Web3.to_checksum_address(
        get_token_contract_address(network, token)
    )

    contract = web3.eth.contract(
        address=contract_address,
        abi=ERC20_ABI
    )

    raw_balance = contract.functions.balanceOf(wallet_address).call()
    decimals = contract.functions.decimals().call()
    symbol = contract.functions.symbol().call()
    name = contract.functions.name().call()

    balance = raw_balance / (10 ** decimals)

    return {
        "type": "erc20",
        "network": network,
        "wallet_address": wallet_address,
        "contract_address": contract_address,
        "token": token.upper(),
        "name": name,
        "symbol": symbol,
        "decimals": decimals,
        "raw_balance": str(raw_balance),
        "balance": balance,
    }

def get_wallet_portfolio(address: str, network: str = "polygon"):
    native_balance = get_native_balance(address, network)

    tokens = TOKENS.get(network.lower(), {})
    token_balances = []

    for token in tokens.keys():
        try:
            token_balances.append(
                get_erc20_balance(address, token, network)
            )
        except Exception as error:
            token_balances.append({
                "token": token.upper(),
                "error": str(error)
            })

    return {
        "network": network,
        "address": Web3.to_checksum_address(address),
        "native": native_balance,
        "tokens": token_balances
    }