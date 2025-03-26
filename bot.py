import time
import sys
import signal
import schedule
from web3 import Web3
from contracts import ContractManager
from config import ContractConfig
import logging
from typing import Tuple, Optional

# Configure logging with colors
class ColorFormatter(logging.Formatter):
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    green = "\x1b[38;5;40m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"

    def __init__(self):
        super().__init__()
        self.fmt = "%(message)s"
        self.FORMATS = {
            logging.DEBUG: self.grey + self.fmt + self.reset,
            logging.INFO: self.fmt,
            logging.WARNING: self.yellow + self.fmt + self.reset,
            logging.ERROR: self.red + self.fmt + self.reset,
            logging.CRITICAL: self.bold_red + self.fmt + self.reset
        }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)

# Set up handler with the custom formatter
handler = logging.StreamHandler()
handler.setFormatter(ColorFormatter())

# Configure root logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)
logger.handlers = [handler]  # Remove any existing handlers


class ApesWinBot:
    def __init__(self, private_key=None):
        self.contract_manager = ContractManager(private_key)
        self.base_bet_amount = None  # Will be set on first run
        self.win_streak = 0  # Track consecutive wins for win streak strategy
        self.loss_streak = 0  # Track consecutive losses
        self.max_bet_percentage = 0.25  # Maximum bet as percentage of balance (25%)
        self.min_bet_percentage = 0.10  # Minimum bet as percentage of balance (10%)
        self.win_streak_rate = 0.20  # Increase bet by 20% for each win
        self.loss_recovery_rate = 0.15  # Increase bet by 15% for each loss
        self.all_time_high = 0  # Track highest balance
        
        # Initialize 69 pattern tracking
        self.games_since_69 = 0  # Number of games since last 69 pattern
        self.chase_69_threshold = 15  # Start chasing after this many games
        self.chase_69_multiplier = 1.1  # Increase bet by 10% for each game over threshold
        
        # Session tracking
        self.session_start_balance = 0  # Will be set on first run
        self.session_games = 0  # Total games this session
        
    def update_wallet(self, private_key):
        """Update the wallet with a new private key"""
        try:
            wallet_address = self.contract_manager.update_private_key(private_key)
            
            # Reset stats when wallet changes
            self.win_streak = 0
            self.loss_streak = 0
            self.games_since_69 = 0
            
            # Update session balance for profit tracking
            try:
                current_balance = self.contract_manager.format_bananas(
                    self.contract_manager.get_banana_balance()
                )
                self.session_start_balance = float(current_balance)
                logging.info(f"Wallet updated with balance: {current_balance} 🍌")
            except Exception as e:
                logging.error(f"Error getting initial balance after wallet update: {e}")
                
            return wallet_address
        except Exception as e:
            logging.error(f"Error updating wallet: {e}")
            raise ValueError(f"Failed to update wallet: {e}")
    
    def format_bananas(self, amount):
        """Convert wei amount to readable banana format
        
        Args:
            amount: Amount in wei
            
        Returns:
            float: Formatted amount in banana units
        """
        try:
            # Convert to float first to ensure numeric value
            return float(amount) / 1e18
        except (ValueError, TypeError):
            logging.error(f"Error formatting banana amount: {amount}")
            return 0.0
        
    def wait_for_game_result(self, game_id: int, initial_balance: int) -> Tuple[bool, int, Optional[list]]:
        """Wait for game result and return outcome
        
        Returns:
            Tuple[bool, int, Optional[list]]: (won, balance_change, dice_results)
        """
        logging.info("⏳ Rolling dice...")
        
        while True:
            # Get game result
            result = self.contract_manager.get_game_result(game_id)
            if result:
                balance_change = result['total_winnings'] - result['total_bet']
                won = balance_change > 0
                
                # Log the result with improved formatting
                dice_str = ", ".join(str(d) for d in result['dice_results'])
                logging.info(f"\n🎲 DICE RESULTS: [{dice_str}]")
                
                if won:
                    logging.info(f"✨ RESULT: WIN! +{self.format_bananas(balance_change)} 🍌")
                else:
                    logging.info(f"📉 RESULT: LOSS -{self.format_bananas(abs(balance_change))} 🍌")
                    
                # Display updated balance with visual indicator of change
                new_balance = initial_balance + balance_change
                percent_change = (balance_change / initial_balance) * 100 if initial_balance > 0 else 0
                
                return won, balance_change, result['dice_results']
            
            # Check every second
            time.sleep(1)
    
    def play_dice_game(self):
        """Execute dice game strategy"""
        try:
            # Get initial balance before bet
            initial_balance = self.contract_manager.get_banana_balance()
            
            # Initialize session data on first run
            if self.session_start_balance is None:
                self.session_start_balance = initial_balance
                self.all_time_high = initial_balance
            else:
                # Update all-time high if we have a new high
                self.all_time_high = max(self.all_time_high, initial_balance)
            
            if initial_balance < ContractConfig.SAFETY_THRESHOLD:
                logging.info(f"⚠️ Balance below safety threshold ({self.format_bananas(ContractConfig.SAFETY_THRESHOLD)} 🍌), skipping bet")
                return
            
            # Set initial base bet on first run
            if self.base_bet_amount is None:
                self.base_bet_amount = max(
                    ContractConfig.MIN_BET_AMOUNT,
                    int(initial_balance * self.min_bet_percentage)  # Start with minimum percentage
                )
                logging.info(f"🎯 Initial bet set to {self.format_bananas(self.base_bet_amount)} 🍌 ({(self.base_bet_amount / initial_balance * 100):.1f}% of balance)")
            
            # Safety check - if balance is too low for base bet
            if initial_balance < self.base_bet_amount:
                logging.warning("⚠️ Balance too low for current bet! Resetting...")
                self.base_bet_amount = max(
                    ContractConfig.MIN_BET_AMOUNT,
                    int(initial_balance * ContractConfig.MAX_BET_PERCENTAGE)
                )
                logging.info(f"🎯 New bet amount: {self.format_bananas(self.base_bet_amount)} 🍌")
            
            # Place bet using base amount
            logging.info("\n" + "="*50)
            logging.info(f"🎲 PLACING BET 🎲")
            logging.info("-"*50)
            logging.info(f"💰 BALANCE")
            logging.info(f"   Current:  {self.format_bananas(initial_balance):>10} 🍌")
            logging.info(f"   All-Time: {self.format_bananas(max(initial_balance, self.all_time_high)):>10} 🍌 {'📈 NEW HIGH!' if initial_balance > self.all_time_high else ''}")
            logging.info(f"\n📊 STRATEGY")
            logging.info(f"   Win Streak:   {self.win_streak}x {'🔥' * min(self.win_streak, 5)}")
            logging.info(f"   Loss Streak:  {self.loss_streak}x {'📉' * min(self.loss_streak, 5)}")
            logging.info(f"   69 Drought:   {self.games_since_69}x {'🌟' if self.games_since_69 >= self.chase_69_threshold else ''}")
            # Calculate multipliers
            win_bonus = 1.0
            recovery = 1.0
            chase_bonus = 1.0
            
            # Apply win streak bonus
            if self.win_streak > 0:
                win_bonus = min(1.0 + (self.win_streak * self.win_streak_rate), 2.0)  # Cap at 2x
                logging.info(f"   Win Streak:   {self.win_streak}x (Bonus: {win_bonus:.2f}x) 🔥")
            
            # Apply loss recovery
            if self.loss_streak > 0:
                recovery = min(1.0 + (self.loss_streak * self.loss_recovery_rate), 2.0)  # Cap at 2x
                logging.info(f"   Recovery:     {recovery:.2f}x")
                
            # Add 69 pattern chasing bonus if we're in a drought
            if self.games_since_69 >= self.chase_69_threshold:
                games_over = self.games_since_69 - self.chase_69_threshold + 1
                chase_bonus = min(self.chase_69_multiplier ** games_over, 3.0)  # Cap at 3x
                logging.info(f"   69 Chase:     {chase_bonus:.2f}x 🌟")
            
            # Apply all multipliers to base bet amount
            actual_bet = int(self.base_bet_amount * win_bonus * recovery * chase_bonus)
            
            # Cap the bet at max percentage
            max_allowed_bet = int(initial_balance * self.max_bet_percentage)
            if actual_bet > max_allowed_bet:
                logging.info(f"   ⚠️ Bet capped at {self.max_bet_percentage*100}% of balance")
                actual_bet = max_allowed_bet
            
            logging.info(f"\n🎯 BET DETAILS")
            logging.info(f"   Base Amount:  {self.format_bananas(self.base_bet_amount):>10} 🍌")
            logging.info(f"   Final Amount: {self.format_bananas(actual_bet):>10} 🍌")
            logging.info(f"   Percentage:   {(actual_bet / initial_balance * 100):>9.1f}%")
            logging.info("="*50)
            game_id = self.contract_manager.place_dice_bet(actual_bet)
            
            # If bet failed, return None to trigger delay
            if game_id is None:
                return None
                
            # Wait for game result
            won, balance_change, dice_results = self.wait_for_game_result(game_id, initial_balance)
            
            # If result is None, something went wrong
            if dice_results is None:
                return None
                
            # Get dice result first
            dice_result = []
            if dice_results and len(dice_results) == 3:
                # Create bitmask like contract
                bit_dice = 0
                double3 = False
                for num in dice_results:
                    # Check for double 3
                    if num == 3 and (bit_dice & (1 << num)) != 0:
                        double3 = True
                    bit_dice |= (1 << num)
                    dice_result.append(num)
                
                # Check for 69 pattern: combinations of 6,9 or 6,3 (without double 3)
                # First handle: 6+9 pattern (note: dice go from 1-6)
                has_six = 6 in dice_result
                has_nine = False  # Since dice are 1-6, we check for combinations that add to 9
                
                # Check for combinations that sum to 9 (like 3+6, 4+5)
                for i in range(len(dice_result)):
                    for j in range(i+1, len(dice_result)):
                        if dice_result[i] + dice_result[j] == 9:
                            has_nine = True
                
                # Also check standard contract patterns: (bitDice == 72 && !double3) || bitDice == 112
                # 72 = 64 (bit 6) + 8 (bit 3) = pattern with 6,3,3
                # 112 = 64 (bit 6) + 32 (bit 5) + 16 (bit 4) = pattern with 6,5,4 (includes 69)
                contract_pattern = (bit_dice == 72 and not double3) or bit_dice == 112
                
                if has_six and has_nine or contract_pattern:
                    is_69_win = True
                    logging.info(f"\n🌟 69 PATTERN!")
                    self.games_since_69 = 0
                else:
                    self.games_since_69 += 1
            
            # Log dice results
            logging.info(f"\n🎲 DICE RESULTS: {dice_result}")
            
            # Update win/loss streaks based on balance change
            if balance_change > 0:
                self.win_streak += 1
                self.loss_streak = 0  # Reset loss streak
                win_bonus = min(1.0 + (self.win_streak * self.win_streak_rate), 2.0)  # Cap at 2x
                logging.info(f"✨ WIN: +{self.format_bananas(balance_change)} 🍌")
                logging.info(f"🔥 WIN STREAK: {self.win_streak}x (Next bonus: {win_bonus:.2f}x)")
            else:
                self.loss_streak += 1
                self.win_streak = 0  # Reset win streak
                recovery_multiplier = min(1.0 + (self.loss_streak * self.loss_recovery_rate), 2.0)  # Cap at 2x
                logging.info(f"📉 LOSS: -{self.format_bananas(abs(balance_change))} 🍌")
                logging.info(f"📉 LOSS STREAK: {self.loss_streak}x (Next recovery: {recovery_multiplier:.2f}x)")
            
            # Calculate next bet
            new_balance = initial_balance + balance_change
            
            # Apply 69 chase bonus
            if self.games_since_69 >= self.chase_69_threshold:
                games_over = self.games_since_69 - self.chase_69_threshold + 1
                chase_bonus = min(self.chase_69_multiplier ** games_over, 3.0)  # Cap at 3x
                logging.info(f"🌟 69 DROUGHT: {self.games_since_69}x (Chase: {chase_bonus:.2f}x)")
            
            # Combine multipliers and cap at max percentage
            bet_percentage = min(
                self.min_bet_percentage * 
                recovery_multiplier * 
                chase_bonus, 
                self.max_bet_percentage
            )
            
            # Calculate next bet
            self.base_bet_amount = max(
                ContractConfig.MIN_BET_AMOUNT,
                int(new_balance * bet_percentage)
            )
            
            logging.info(f"🎯 NEXT BET: {self.format_bananas(self.base_bet_amount)} 🍌 ({(self.base_bet_amount / new_balance * 100):.1f}%)")
            
            # Return game information for dashboard
            return {
                'game_id': game_id,
                'dice': dice_result,
                'won': balance_change > 0,
                'bet_amount': self.format_bananas(self.base_bet_amount),
                'balance_change': self.format_bananas(abs(balance_change)),
                'is_69': is_69_win if 'is_69_win' in locals() else False
            }
                
        except ValueError as e:
            if "Failed to approve" in str(e):
                logging.error("Failed to approve dice game contract. Waiting 5 seconds...")
                time.sleep(5)
            else:
                logging.error(f"Error playing dice game: {e}")
                time.sleep(1)
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            time.sleep(1)
    
    def run(self):
        """Main bot loop"""
        logging.info("\n🎲 APES.WIN DICE BOT")
        
        initial_balance = self.contract_manager.get_banana_balance()
        native_balance = self.contract_manager.get_native_balance()
        
        logging.info(f"\n💰 🍌 {self.format_bananas(initial_balance)} | 💎 {self.contract_manager.format_native(native_balance):.4f} S")
        
        while True:
            try:
                # Play a game
                result = self.play_dice_game()
                
                # Normal delay between bets
                time.sleep(5)
                    
            except Exception as e:
                logging.error(f"❌ {e}")
                logging.info("⏳ Error occurred, waiting 30s...")
                time.sleep(30)

def signal_handler(sig, frame):
    logging.info("\n\n⛔️ Shutting down bot...")
    sys.exit(0)

if __name__ == "__main__":
    # Set up signal handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    bot = ApesWinBot()
    try:
        bot.run()
    except KeyboardInterrupt:
        logging.info("\n\n⛔️ Shutting down bot...")
        sys.exit(0)
