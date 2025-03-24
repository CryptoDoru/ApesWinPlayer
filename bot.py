import time
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
    def __init__(self):
        self.contract_manager = ContractManager()
        self.base_bet_amount = None  # Will be set on first run
        self.win_streak = 0  # Track consecutive wins
        self.loss_streak = 0  # Track consecutive losses
        self.max_bet_percentage = 0.25  # Maximum bet as percentage of balance (25%)
        self.min_bet_percentage = 0.10  # Minimum bet as percentage of balance (10%)
        self.streak_multiplier = 1.2  # Multiply bet by this on win streaks
        self.all_time_high = 0  # Track highest balance
        self.session_start_balance = None  # Track starting balance for session
        self.games_since_69 = 0  # Track games since last 69 pattern
        self.chase_69_threshold = 15  # Start chasing 69 after this many games
        self.chase_69_multiplier = 1.1  # Increase bet by 10% for each game after threshold
    
    def format_bananas(self, amount):
        """Convert wei amount to readable banana format"""
        return f"{amount / 1e18:.3f}"
        
    def wait_for_game_result(self, game_id: int, initial_balance: int) -> Tuple[bool, int, Optional[list]]:
        """Wait for game result and return outcome
        
        Returns:
            Tuple[bool, int, Optional[list]]: (won, balance_change, dice_results)
        """
        logging.info("⏳ Rolling dice...")
        
        # Try harder to wait for the result
        max_attempts = 45  # 90 seconds total
        for attempt in range(max_attempts):
            if self.contract_manager.wait_for_game_fulfillment(game_id):
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
                    
                    logging.info(f"\n💰 BALANCE SUMMARY 💰")
                    logging.info(f"   PREVIOUS: {self.format_bananas(initial_balance)} 🍌")
                    logging.info(f"   CURRENT:  {self.format_bananas(new_balance)} 🍌")
                    logging.info(f"   CHANGE:   {'+' if balance_change >= 0 else '-'}{self.format_bananas(abs(balance_change))} 🍌 ({'+' if percent_change >= 0 else '-'}{abs(percent_change):.1f}%)")
                        
                    return won, balance_change, result['dice_results']
            time.sleep(2)
            
        logging.warning("Game pending fulfillment after extended wait, continuing...")
        return False, 0, None
    
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
            streak_bonus = 1.0
            recovery = 1.0
            chase_bonus = 1.0
            
            if self.win_streak > 0:
                streak_bonus = min(self.streak_multiplier ** (self.win_streak - 1), 2.0)
                logging.info(f"   Streak Bonus: {streak_bonus:.2f}x")
            elif self.loss_streak > 0:
                recovery = min(1.0 + (self.loss_streak * 0.15), 2.0)
                logging.info(f"   Recovery:     {recovery:.2f}x")
                
            # Add 69 pattern chasing bonus if we're in a drought
            if self.games_since_69 >= self.chase_69_threshold:
                games_over = self.games_since_69 - self.chase_69_threshold + 1
                chase_bonus = min(self.chase_69_multiplier ** games_over, 3.0)  # Cap at 3x
                logging.info(f"   69 Chase:     {chase_bonus:.2f}x 🌟")
            
            logging.info(f"\n🎯 BET DETAILS")
            logging.info(f"   Amount:      {self.format_bananas(self.base_bet_amount):>10} 🍌")
            logging.info(f"   Percentage:  {(self.base_bet_amount / initial_balance * 100):>9.1f}%")
            logging.info("="*50)
            game_id = self.contract_manager.place_dice_bet(self.base_bet_amount)
            
            # Wait for game result
            if game_id is not None:
                won, balance_change, dice_results = self.wait_for_game_result(game_id, initial_balance)
                
                if won:
                    # Increment win streak, reset loss streak
                    self.win_streak += 1
                    self.loss_streak = 0
                    
                    # Track games since 69 pattern
                    self.games_since_69 += 1
                    
                    # Check for 69 pattern win
                    is_69_win = False
                    if dice_results and len(dice_results) == 3:
                        # Create bitmask like contract
                        bit_dice = 0
                        double3 = False
                        for num in dice_results:
                            # Check for double 3
                            if num == 3 and (bit_dice & (1 << num)) != 0:
                                double3 = True
                            bit_dice |= (1 << num)
                        
                        # Check for 69 pattern: (bitDice == 72 && !double3) || bitDice == 112
                        # 72 = 64 (bit 6) + 8 (bit 3) = pattern with 6,3,3
                        # 112 = 64 (bit 6) + 32 (bit 5) + 16 (bit 4) = pattern with 6,5,4 (includes 69)
                        if (bit_dice == 72 and not double3) or bit_dice == 112:
                            is_69_win = True
                            logging.info(f"\n🌟🌟🌟 69 PATTERN WIN! 🌟🌟🌟")
                            logging.info(f"   WIN AMOUNT: +{self.format_bananas(balance_change)} 🍌")
                            logging.info(f"   DROUGHT ENDED: {self.games_since_69} games")
                            self.games_since_69 = 0  # Reset counter
                            
                    # Calculate new bet based on win streak and 69 chase
                    new_balance = initial_balance + balance_change
                    streak_bonus = min(self.streak_multiplier ** (self.win_streak - 1), 2.0)  # Cap at 2x
                    
                    # Add 69 chase multiplier if in drought
                    chase_bonus = 1.0
                    if self.games_since_69 >= self.chase_69_threshold:
                        games_over = self.games_since_69 - self.chase_69_threshold + 1
                        chase_bonus = min(self.chase_69_multiplier ** games_over, 3.0)  # Cap at 3x
                    
                    # Combine multipliers and cap at max percentage
                    bet_percentage = min(self.min_bet_percentage * streak_bonus * chase_bonus, self.max_bet_percentage)
                    
                    self.base_bet_amount = max(
                        ContractConfig.MIN_BET_AMOUNT,
                        int(new_balance * bet_percentage)
                    )
                    
                    if is_69_win:
                        # On 69 pattern win, be extra aggressive
                        self.base_bet_amount = int(self.base_bet_amount * 1.5)
                        
                    logging.info(f"   🎯 NEW BET: {self.format_bananas(self.base_bet_amount)} 🍌 ({(self.base_bet_amount / new_balance * 100):.1f}% of balance)")
                    logging.info(f"   🔥 WIN STREAK: {self.win_streak}x (Bonus: {streak_bonus:.2f}x)")
                    
                    if not is_69_win:
                        new_balance = initial_balance + balance_change
                        win_percent = (balance_change / initial_balance * 100)
                        logging.info(f"\n✨ WINNER! ✨")
                        logging.info(f"   WIN AMOUNT:   +{self.format_bananas(balance_change)} 🍌 ({win_percent:+.1f}%)")
                        logging.info(f"   NEW BALANCE:   {self.format_bananas(new_balance)} 🍌")
                        if new_balance > self.all_time_high:
                            logging.info(f"   🏆 NEW ALL-TIME HIGH! Previous: {self.format_bananas(self.all_time_high)} 🍌")
                else:
                    # Reset win streak, increment loss streak
                    self.win_streak = 0
                    self.loss_streak += 1
                    
                    # Track games since 69 pattern
                    self.games_since_69 += 1
                    
                    if balance_change < 0:
                        new_balance = initial_balance + balance_change
                        loss_percent = (balance_change / initial_balance * 100)
                        logging.info(f"\n📉 LOSS 📉")
                        logging.info(f"   LOSS AMOUNT:  -{self.format_bananas(abs(balance_change))} 🍌 ({loss_percent:+.1f}%)")
                        logging.info(f"   NEW BALANCE:   {self.format_bananas(new_balance)} 🍌")
                        # Only show drawdown metrics if we have a valid all-time high
                        if self.all_time_high > 0:
                            logging.info(f"   PEAK BALANCE:  {self.format_bananas(self.all_time_high)} 🍌")
                            drawdown = ((self.all_time_high - new_balance) / self.all_time_high * 100) if self.all_time_high > 0 else 0
                            logging.info(f"   MAX DRAWDOWN:  {drawdown:.1f}%")
                        
                        # Aggressive recovery strategy
                        new_balance = initial_balance + balance_change
                        recovery_multiplier = min(1.0 + (self.loss_streak * 0.15), 2.0)  # +15% per loss, cap at 2x
                        
                        # Add 69 chase multiplier if in drought
                        chase_bonus = 1.0
                        if self.games_since_69 >= self.chase_69_threshold:
                            games_over = self.games_since_69 - self.chase_69_threshold + 1
                            chase_bonus = min(self.chase_69_multiplier ** games_over, 3.0)  # Cap at 3x
                        
                        # Combine multipliers and cap at max percentage
                        bet_percentage = min(self.min_bet_percentage * recovery_multiplier * chase_bonus, self.max_bet_percentage)
                        
                        self.base_bet_amount = max(
                            ContractConfig.MIN_BET_AMOUNT,
                            int(new_balance * bet_percentage)
                        )
                        
                        logging.info(f"   🎯 RECOVERY BET: {self.format_bananas(self.base_bet_amount)} 🍌 ({(self.base_bet_amount / new_balance * 100):.1f}% of balance)")
                        logging.info(f"   📉 LOSS STREAK: {self.loss_streak}x (Recovery: {recovery_multiplier:.2f}x)")
                    else:
                        logging.info("\n❌ GAME FAILED ❌")
                
                # Display current balance
                new_balance = initial_balance + balance_change
                logging.info(f"\n💰 UPDATED BALANCE: {self.format_bananas(new_balance)} 🍌")
                logging.info(f"   CHANGE: {'+' if balance_change >= 0 else '-'}{self.format_bananas(abs(balance_change))} 🍌")
                
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
        logging.info("\n" + "="*50)
        logging.info("🎲 APES.WIN DICE BOT STARTED 🎲")
        logging.info("="*50)
        
        initial_balance = self.contract_manager.get_banana_balance()
        native_balance = self.contract_manager.get_native_balance()
        
        logging.info(f"\n💰 BALANCE SUMMARY 💰")
        logging.info(f"   🍌 Bananas: {self.format_bananas(initial_balance)}")
        logging.info(f"   💎 S Token: {self.contract_manager.format_native(native_balance):.4f}")
        
        while True:
            try:
                self.play_dice_game()
            except Exception as e:
                logging.error(f"❌ {e}")
                # On error, wait 30 seconds before retrying
                logging.info("⏳ Error occurred, waiting 30s...")
                time.sleep(30)

if __name__ == "__main__":
    bot = ApesWinBot()
    bot.run()
