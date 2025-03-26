from typing import Dict, ClassVar
from web3 import Web3

class ContractConfig:
    SONIC_RPC_URL = "https://rpc.soniclabs.com"
    
    # Contract Address - Season 2 Dice Game Contract
    CONTRACT_ADDRESS = "0x40A94AB8Aac840Be65B22Ac857A78ac56447db5f"
    DICE_GAME_ADDRESS = CONTRACT_ADDRESS
    BANANA_TOKEN_ADDRESS = CONTRACT_ADDRESS
    CHAIN_ID = 146
    
    # Contract ABIs - Note: This is a combined contract that handles both dice game and token functionality
    DICE_GAME_ABI: ClassVar[list] = [
        {
            "inputs": [{"name": "_betAmts", "type": "uint256[]"}],
            "name": "bet",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [{"name": "_inputs", "type": "bytes"}],
            "name": "bet",
            "outputs": [],
            "stateMutability": "payable",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "gameNotOver",
            "outputs": [{"name": "", "type": "bool"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [
                {"name": "spender", "type": "address"},
                {"name": "amount", "type": "uint256"}
            ],
            "name": "approve",
            "outputs": [],
            "stateMutability": "nonpayable",
            "type": "function"
        },
        {
            "inputs": [
                {"name": "owner", "type": "address"},
                {"name": "spender", "type": "address"}
            ],
            "name": "allowance",
            "outputs": [{"name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "getGameState",
            "outputs": [{
                "components": [
                    {"name": "gameId", "type": "uint256"},
                    {"name": "betNumber", "type": "uint256"}
                ],
                "name": "state",
                "type": "tuple[]"
            }],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"name": "user", "type": "address"}],
            "name": "getUserLastGameInfo",
            "outputs": [
                {"name": "id", "type": "uint256"},
                {
                    "components": [
                        {"name": "fulfilled", "type": "bool"},
                        {"name": "user", "type": "address"},
                        {"name": "totalBet", "type": "uint256"},
                        {"name": "totalWinnings", "type": "uint256"},
                        {"name": "betAmts", "type": "uint256[]"},
                        {"name": "diceRollResult", "type": "uint256[]"}
                    ],
                    "name": "round",
                    "type": "tuple"
                }
            ],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [{"name": "_gameId", "type": "uint256"}],
            "name": "getGameRoundInfo",
            "outputs": [{
                "components": [
                    {"name": "fulfilled", "type": "bool"},
                    {"name": "user", "type": "address"},
                    {"name": "totalBet", "type": "uint256"},
                    {"name": "totalWinnings", "type": "uint256"},
                    {"name": "betAmts", "type": "uint256[]"},
                    {"name": "diceRollResult", "type": "uint256[]"}
                ],
                "name": "gameInfo",
                "type": "tuple"
            }],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": False, "name": "gameId", "type": "uint256"},
                {"indexed": False, "name": "user", "type": "address"},
                {"indexed": False, "name": "totalBetAmt", "type": "uint256"}
            ],
            "name": "Bet",
            "type": "event"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": False, "name": "from", "type": "address"},
                {"indexed": False, "name": "pointsAmount", "type": "uint256"}
            ],
            "name": "BurnPoints",
            "type": "event"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": False, "name": "to", "type": "address"},
                {"indexed": False, "name": "pointsAmount", "type": "uint256"}
            ],
            "name": "MintPoints",
            "type": "event"
        }
    ]
    
    # Since this is a combined contract, we use the same ABI for both
    BANANA_TOKEN_ABI: ClassVar[list] = DICE_GAME_ABI

    # Game Parameters
    MIN_BET_AMOUNT = 1
    MAX_BET_PERCENTAGE = 0.10  # 10% of balance
    SAFETY_THRESHOLD = 1000  # Minimum balance to maintain
    
    # Initialize Web3
    @staticmethod
    def get_web3():
        return Web3(Web3.HTTPProvider(ContractConfig.SONIC_RPC_URL))
