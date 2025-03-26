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

### Season 2 Improved Strategies
- **Balanced Risk**: Optimized for the new Apes Win Season 2 mechanics
- **Volatility Management**: Adaptive bet sizing based on real-time performance
- **Visual Pattern Recognition**: Enhanced dashboard for pattern detection

### Base Strategy
- Starting bet: 10% of balance (configurable in dashboard)
- Maximum bet: 25% of balance (adjustable for risk tolerance)
- Minimum bet: Configurable safety threshold with auto-stop feature

### Win Streak Strategy
- +20% bet increase per consecutive win
- Capped at 2x the base bet
- Resets on loss
- Visual indicators in dashboard

### Loss Recovery
- +15% bet increase per consecutive loss
- Capped at 2x the base bet
- Intelligent bankroll management
- Automatic recovery pacing

### 69 Pattern Chasing
- Activates after 15 games without 69 pattern (10x multiplier)
- Progressive bet increases (10% per game)
- Capped at 3x multiplier
- Resets on pattern hit
- Real-time tracking with visual indicators

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
