# 🎲 Apes.win Dice Bot - Season 2

An advanced automated betting bot for the Apes.win Dice Game featuring a web dashboard, wallet connection, and smart bankroll management strategies. Updated for Apes Win Season 2!

## ✨ Features

### 🌐 Web Dashboard (New for Season 2)
- **Browser Interface**: Control the bot from any device without coding
- **Real-time Stats**: Live tracking of balances, streaks, and performance
- **Wallet Connection**: Connect with your private key directly in the UI
- **Game Log**: View game history with detailed results
- **Mobile Friendly**: Responsive design for desktop and mobile devices

### 🎯 Smart Betting Strategies
- **Dynamic Bet Sizing**: Automatically adjusts bets between 10-25% of balance
- **Win Streak Bonus**: Increases bets during winning streaks (up to 2x)
- **Loss Recovery**: Smart recovery system during losing streaks (+15% per loss)
- **69 Pattern Chasing**: Increases bets after 15 games without 10x wins

### 📊 Advanced Analytics
- Real-time balance tracking with session performance
- All-time high and drawdown monitoring
- Win/Loss streak tracking with visual indicators
- Detailed bet analysis and strategy metrics
- Visual patterns in game history

### ⚡ Gas Optimization
- Optimized transaction parameters (300k gas limit)
- Minimum required value for callbacks
- Up to 32% reduction in transaction costs

## 🚀 Getting Started

### Online Dashboard (Quickest Method)

Visit the live dashboard at [https://apes-win-player.vercel.app](https://apes-win-player.vercel.app) to access the bot without installation:

1. Enter your wallet private key in the connection form
2. View your current balances
3. Start the bot and watch your games in real-time
4. Track stats and performance metrics

### Local Installation

#### Prerequisites
- Python 3.9+
- pip (Python package installer)

#### Installation

1. Clone the repository:
```bash
git clone https://github.com/CryptoDoru/ApesWinPlayer.git
cd ApesWinPlayer
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the web dashboard:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5556
```

5. Connect your wallet using the private key input field

### Traditional CLI Mode (Legacy)

If you prefer to run the bot without the web interface:

1. Configure environment:
```bash
cp .envexample .env
```

2. Edit `.env` and add your private key:
```
PRIVATE_KEY=your_private_key_here
```

3. Run the bot:
```bash
python bot.py
```

## 📈 Strategy Details

### Season 2 Optimized Strategy

This bot employs a sophisticated betting strategy designed specifically for Apes Win Season 2 dice mechanics. The strategy dynamically adjusts bet sizes based on game patterns and streak analysis.

### Default Betting Strategy (Core Algorithm)

```python
# Actual code from bot.py (simplified)
def calculate_next_bet(balance, loss_streak, games_since_69):
    # Base bet starts at 10% of balance
    base_percentage = 0.10  # min_bet_percentage
    
    # Apply loss recovery multiplier
    if loss_streak > 0:
        recovery_multiplier = min(1.0 + (loss_streak * 0.15), 2.5)  # +15% per loss, cap at 2.5x
    else:
        recovery_multiplier = 1.0
        
    # Apply 69 pattern chase bonus
    if games_since_69 >= 15:  # chase_69_threshold
        games_over = games_since_69 - 15 + 1
        chase_bonus = min(1.1 ** games_over, 3.0)  # +10% compounding, cap at 3x
    else:
        chase_bonus = 1.0
        
    # Calculate final percentage (capped at max 25%)
    bet_percentage = min(
        base_percentage * recovery_multiplier * chase_bonus,
        0.25  # max_bet_percentage
    )
    
    # Calculate actual bet amount
    bet_amount = max(MIN_BET_AMOUNT, int(balance * bet_percentage))
    
    return bet_amount
```

### Base Strategy Details
- **Starting Bet**: 10% of current balance (adjustable)
- **Minimum Bet**: Never goes below a configurable safety threshold (defaults to 500)
- **Maximum Bet**: Capped at 25% of balance to prevent over-betting
- **Safety Threshold**: Auto-stops betting when balance falls below minimum threshold

### Loss Recovery System
- Each consecutive loss increases bet by **15%** (multiplicative)
- Formula: `base_bet * (1 + (loss_streak * 0.15))`
- Hard cap at **2.5x** the base bet to prevent excessive risk
- Automatically resets after any win
- Example progression:
  - 1st loss: 1.15x base bet
  - 2nd loss: 1.30x base bet
  - 3rd loss: 1.45x base bet
  - 10th loss: 2.5x base bet (capped)

### 69 Pattern Detection & Chasing
- Identifies the valuable "69" pattern that yields **10x multipliers**
- Detection logic checks for:
  - Combinations that sum to 9 (e.g., 3+6, 4+5)
  - Presence of 6 in the dice results
  - Contract-specific bit patterns (72 without double 3, or 112)
- After **15 consecutive games** without hitting the pattern, activates chase mode:
  - Increases bet by compounding 10% per game over threshold
  - Formula: `base_bet * (1.1 ^ (games_over_threshold))`
  - Hard cap at **3x** the base bet
  - Resets immediately when the pattern is hit
- Example progression:
  - After 15 games: 1.1x base bet
  - After 20 games: 1.61x base bet
  - After 25 games: 2.65x base bet
  - After 30 games: 3.0x base bet (capped)

### Strategy Combinations
- **Multiple multipliers stack**: Loss recovery and 69 chase can combine
- **Global cap**: Final bet is always capped at 25% of balance regardless of multipliers
- **Minimal intervention**: Strategy runs autonomously once configured

## 📝 Configuration

### Web Dashboard Configuration (New for Season 2)
- **Visual Settings Panel**: Easy configuration without code editing
- **Real-time Adjustments**: Change strategy parameters without restarting
- **Profile System**: Save and load different strategy configurations
- **Mobile Settings**: Adjust all parameters from any device

### Advanced Settings Options
- **Safety Threshold**: Minimum balance to continue betting (prevents over-betting)
- **Bet Percentage Range**: Customize risk from conservative (5-15%) to aggressive (15-30%)
- **Win/Loss Patterns**: Configure how the bot reacts to streaks
- **69 Chase Settings**: Adjust when and how aggressively to chase 10x multipliers
- **Auto-Stop Conditions**: Set balance targets to automatically pause the bot

### Developer Configuration
For developers modifying the code:
- `config.py`: Global configuration and API settings
- `bot.py`: Strategy implementation parameters
- `app.py`: Web server and API configuration
- `contracts.py`: Blockchain interaction settings

## 📊 Dashboard & Analytics

### Real-time Dashboard (New for Season 2)
- **Balance Graph**: Visual representation of balance over time
- **Game History**: Detailed log of each game with results and bet amounts
- **Streak Indicators**: Visual tracking of current win/loss streaks
- **Performance Metrics**: Win rate, average bet size, and expected value
- **Pattern Analysis**: Visualization of 69 pattern occurrences

### Mobile Analytics
- Full dashboard functionality on mobile devices
- Lightweight design for minimal data usage
- Push notifications for significant events (optional)

## ⚠️ Security

### Wallet Protection
- **Private Key Handling**: Keys are never stored on the server
- **Session Storage**: Temporary browser-only storage (cleared on close)
- **No Backend Storage**: Your keys never leave your device
- **SSL Encryption**: All communications are encrypted

### Best Practices
- Never share your private key with anyone
- Use a dedicated wallet with limited funds for betting
- Regularly monitor your transactions
- Always test with small amounts first
- Log out when not using the dashboard

## ⚖️ Disclaimer

This bot is for educational purposes only. Gambling involves risk. Never bet more than you can afford to lose. Make sure to comply with apes.win terms of service.

## 🤝 Contributing

Contributions welcome! Please read the contributing guidelines before submitting PRs.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
