import time
from web3 import Web3
from eth_account.account import Account
from eth_account.signers.local import LocalAccount
from eth_abi import encode
from config import ContractConfig
import os
from dotenv import load_dotenv
from typing import Dict, Tuple, Optional
import logging

load_dotenv()

class ContractManager:
    def __init__(self, private_key=None):
        self.web3 = ContractConfig.get_web3()
        self.private_key = None
        
        # Use provided private key or get from environment variables
        if not private_key:
            private_key = os.getenv("PRIVATE_KEY")
            if not private_key:
                # Create a dummy account with no funds
                self.account = Account.create()
                # Initialize contract (combined dice game and token contract)
                self.contract = self.web3.eth.contract(
                    address=ContractConfig.CONTRACT_ADDRESS,
                    abi=ContractConfig.DICE_GAME_ABI
                )
                # Track current game ID
                self.current_game_id = None
                return
        
        # Store the private key
        self.private_key = private_key
            
        # Initialize account with private key
        self.account: LocalAccount = Account.from_key(private_key)
        
        # Initialize contract (combined dice game and token contract)
        self.contract = self.web3.eth.contract(
            address=ContractConfig.CONTRACT_ADDRESS,
            abi=ContractConfig.DICE_GAME_ABI
        )
        
        # Track current game ID
        self.current_game_id = None
        
    def update_private_key(self, private_key):
        """Update the account with a new private key"""
        if not private_key:
            raise ValueError("Private key cannot be empty")
        
        # Basic validation for private key format
        if not private_key.startswith('0x') or len(private_key) != 66:
            raise ValueError("Invalid private key format")
            
        try:
            # Try to create account first to validate the private key
            new_account = Account.from_key(private_key)
            
            # If we get here, the private key is valid
            self.private_key = private_key
            self.account = new_account
            
            # Re-initialize the contract with the new account
            self.contract = self.web3.eth.contract(
                address=ContractConfig.CONTRACT_ADDRESS,
                abi=ContractConfig.DICE_GAME_ABI
            )
            
            logging.info(f"Wallet connected successfully: {self.account.address}")
            return self.account.address
        except Exception as e:
            logging.error(f"Error updating private key: {e}")
            raise ValueError(f"Invalid private key: {e}")
    
    def get_native_balance(self) -> int:
        """Get native token (S) balance"""
        return self.web3.eth.get_balance(self.account.address)

    def format_native(self, amount: int) -> float:
        """Format native token amount from wei"""
        return amount / 1e18

    def get_banana_balance(self) -> int:
        """Get Banana balance"""
        return self.contract.functions.balanceOf(self.account.address).call()
        
    def format_bananas(self, amount: int) -> float:
        """Format banana amount from wei to regular number"""
        return amount / 10**18
    
    def get_unfulfilled_games(self) -> list:
        """Get list of unfulfilled games in order
        
        Returns:
            list: List of unfulfilled game IDs in ascending order
        """
        try:
            logging.info("Getting last game info...")
            game_id, fulfilled = self.get_last_game_info()
            if game_id == 0:
                logging.info("No games found")
                return []
            if not fulfilled:
                logging.info(f"Found unfulfilled game {game_id}")
                return [game_id]
            return []
        except Exception as e:
            logging.error(f"Error getting game info: {e}")
            return []
            
    def wait_for_game_fulfillment(self, game_id: int, max_attempts: int = 30) -> bool:
        """Wait for a game to be fulfilled
        
        Args:
            game_id: Game ID to wait for
            max_attempts: Maximum number of attempts to check fulfillment
            
        Returns:
            bool: True if game was fulfilled, False if timed out
        """
        for attempt in range(max_attempts):
            try:
                # Check if any games before this one are unfulfilled
                unfulfilled = self.get_unfulfilled_games()
                if not unfulfilled or unfulfilled[0] > game_id:
                    # All games before this one are fulfilled, check this one
                    result = self.get_game_result(game_id)
                    if result and result['fulfilled']:
                        return True
                time.sleep(2)  # Wait longer between checks
            except Exception as e:
                time.sleep(2)
        return False
    
    def get_last_game_info(self) -> Tuple[int, bool]:
        """Get the last game ID and fulfillment status for the current user
        
        Returns:
            Tuple[int, bool]: (game_id, fulfilled)
        """
        try:
            game_info = self.contract.functions.getUserLastGameInfo(self.account.address).call()
            return game_info[0], game_info[1][0]  # (id, round.fulfilled)
        except Exception as e:
            return 0, True  # No games yet
            
    def get_game_result(self, game_id: int) -> Optional[Dict]:
        """Get detailed game result info
        
        Args:
            game_id: Game ID to get results for
            
        Returns:
            Optional[Dict]: Game result info or None if not found/fulfilled
        """
        # Retry mechanism for blockchain calls
        max_retries = 3
        backoff_time = 0.5  # Start with 0.5 second backoff
        
        for attempt in range(max_retries):
            try:
                # Add a small delay before retries (not on first attempt)
                if attempt > 0:
                    time.sleep(backoff_time)
                    backoff_time *= 2  # Exponential backoff
                    logging.info(f"Retry {attempt}/{max_retries} for game result (game_id: {game_id})")
                
                # Get game info directly
                game_info = self.contract.functions.getUserLastGameInfo(self.account.address).call()
                
                # Handle case where game_id doesn't match
                if game_info[0] != game_id:
                    if attempt == max_retries - 1:  # Only log on last retry
                        logging.warning(f"Game ID mismatch: expected {game_id}, got {game_info[0]}")
                    continue  # Try again
                
                round_info = game_info[1]
                if not round_info[0]:  # not fulfilled
                    if attempt == max_retries - 1:  # Only log on last retry
                        logging.info(f"Game {game_id} not yet fulfilled, waiting...")
                    return {'fulfilled': False, 'game_id': game_id}  # Return partial result
                
                # Successfully got the result
                return {
                    'fulfilled': round_info[0],  # fulfilled
                    'user': round_info[1],       # user address
                    'total_bet': round_info[2],  # totalBet
                    'total_winnings': round_info[3], # totalWinnings
                    'bet_amounts': round_info[4],    # betAmounts
                    'dice_results': round_info[5]    # diceRollResult
                }
            except Exception as e:
                if attempt == max_retries - 1:  # Only log detailed error on last retry
                    logging.error(f"Error getting game result (attempt {attempt+1}/{max_retries}): {e}")
                    # Add more detailed error info on last retry
                    logging.error(f"Detailed error info: {type(e).__name__}")
                else:
                    # Simple log for intermediate retries
                    logging.warning(f"Retrying game result fetch (attempt {attempt+1}/{max_retries})")
        
        logging.error(f"Failed to get game result after {max_retries} attempts for game_id {game_id}")
        return None
    
    def check_bet_amount(self, amount: int) -> bool:
        """Check if we have enough balance for the bet
        
        Args:
            amount: Amount to bet
            
        Returns:
            bool: True if we have enough balance
        """
        try:
            # Check current balance
            balance = self.contract.functions.balanceOf(self.account.address).call()
            return balance >= amount
        except Exception as e:
            logging.error(f"Error checking balance: {e}")
            return False
    
    def place_dice_bet(self, bet_amount: int) -> Optional[int]:
        """Place a bet on the dice game
        
        Returns:
            Optional[int]: Game ID if successful, None if failed
        """
        # Check for any unfulfilled games
        logging.info("Checking for unfulfilled games...")
        unfulfilled = self.get_unfulfilled_games()
        if unfulfilled:
            # Must wait for oldest unfulfilled game since they must be fulfilled in order
            oldest_game = unfulfilled[0]  # Already sorted in ascending order
            if not self.wait_for_game_fulfillment(oldest_game):
                logging.error("Previous game not fulfilled after timeout")
                return None
        
        # Place bet (split bet amount across three dice)
        bet_per_dice = bet_amount // 3  # Split bet evenly across dice
        bet_amounts = [bet_per_dice] * 3
        
        # Optimized transaction parameters from Apes.Win interface
        gas_price = 55000000000  # 55 Gwei (from example transaction)
        gas_limit = 300000  # Keep our current limit, it's already lower than example
        
        # Calculate optimal value to send (from example transaction)
        tx_value = 19250000000000000  # 0.01925 S (from example transaction)
        
        logging.info(f"\n📈 Gas Info:")
        logging.info(f"   Gas Price: {gas_price} wei ({gas_price / 1e9:.2f} gwei)")
        logging.info(f"   Value to Send: {self.format_native(tx_value):.10f} S")
        logging.info(f"   Gas Limit: {gas_limit:,}")
        
        # Check if we have enough balance for the bet
        if not self.check_bet_amount(bet_amount):
            banana_balance = self.get_banana_balance()
            logging.error(f"Insufficient balance ({self.format_bananas(banana_balance)} Bananas) for bet ({self.format_bananas(bet_amount)} Bananas)")
            return None
            
        # Build transaction
        nonce = self.web3.eth.get_transaction_count(self.account.address)
        
        # Estimate gas for the transaction
        logging.info("Estimating gas for bet transaction...")
        try:
            # Use the regular bet function with an array of bet amounts
            # This matches the function signature in the ABI: bet(uint256[])
            transaction = self.contract.functions.bet(bet_amounts)
            
            # Use optimized gas parameters from Apes.Win interface
            gas_price = 55000000000  # 55 Gwei 
            gas_limit = 300000  # Fixed gas limit
            
            # Build transaction with the contract function
            signed_txn = transaction.build_transaction({
                'from': self.account.address,
                'value': tx_value,
                'gas': 300000,  # Fixed gas limit
                'gasPrice': gas_price,
                'nonce': nonce,
                'chainId': ContractConfig.CHAIN_ID
            })
            
        except Exception as e:
            logging.error(f"Failed to estimate gas: {str(e)}")
            return None
        
        # Sign and send transaction
        native_balance = self.get_native_balance()
        logging.info(f"💎 S Balance: {self.format_native(native_balance):.4f} S")
        try:
            signed_tx = self.web3.eth.account.sign_transaction(signed_txn, self.account.key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            if not receipt['status']:
                logging.error(f"Transaction failed: {tx_hash.hex()}")
                return None
                
            # Log actual costs
            gas_used = receipt['gasUsed']
            actual_tx_fee = gas_used * gas_price
            value_sent = tx_value  # Value sent with transaction
            total_cost = actual_tx_fee + value_sent
            
            # Calculate cost savings compared to original settings
            old_gas_limit = 412583  # Original gas limit
            old_gas_price = 55000000000  # Original gas price (55 Gwei)
            old_value = 24750000000000000  # Original value (0.02475 S)
            old_cost = (old_gas_limit * old_gas_price) + old_value
            new_cost = actual_tx_fee + value_sent
            savings = self.format_native(old_cost - new_cost)
            
            logging.info(f"\n🟢 Transaction Success:")
            logging.info(f"   Gas Used: {gas_used:,}")
            logging.info(f"   Gas Cost: {self.format_native(actual_tx_fee):.4f} S")
            logging.info(f"   Value Sent: {self.format_native(value_sent):.4f} S")
            logging.info(f"   Total Cost: {self.format_native(total_cost):.4f} S")
            logging.info(f"   Saved: ~{savings:.4f} S compared to old settings")
                
            # Get game ID from last game info
            game_id, _ = self.get_last_game_info()
            if game_id > 0:
                return game_id
                
            logging.error("Failed to get game ID after successful transaction")
            return None
                
        except Exception as e:
            logging.error(f"Error sending bet transaction: {e}")
            return None

    
    def build_and_send_tx(self, contract_tx, value: int = 0) -> Dict:
        """Helper to build and send a transaction"""
        try:
            # Use optimized gas price from Apes.Win interface
            gas_price = 55000000000  # 55 Gwei
            
            # Build transaction with Season 2 parameters
            tx = contract_tx.buildTransaction({
                'from': self.account.address,
                'chainId': ContractConfig.CHAIN_ID,
                'nonce': self.web3.eth.get_transaction_count(self.account.address),
                'gasPrice': gas_price,
                'gas': 300000,  # Fixed gas limit from successful tx
                'value': value
            })
            
            # Estimate gas with 50% buffer
            try:
                gas_estimate = int(self.web3.eth.estimate_gas(tx) * 1.5)
                tx['gas'] = gas_estimate
            except Exception as e:
                print(f"Gas estimation failed: {e}, using default gas limit")
                tx['gas'] = 500000  # Default gas limit
            
            # Sign and send transaction
            signed_tx = self.web3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.web3.eth.send_raw_transaction(signed_tx.rawTransaction)
            
            # Wait for receipt
            receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
            return receipt
        except Exception as e:
            print(f"Error in transaction: {e}")
            return None
        
        # Wait for receipt and return
        return self.web3.eth.wait_for_transaction_receipt(tx_hash)
