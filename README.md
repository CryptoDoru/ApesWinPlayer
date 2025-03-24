# 🎲 Apes.win Dice Bot

An advanced automated betting bot for the Apes.win Dice Game with optimized strategies and smart bankroll management.

## ✨ Features

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

### ⚡ Gas Optimization
- Optimized transaction parameters (300k gas limit)
- Minimum required value for callbacks
- Up to 32% reduction in transaction costs

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- pip (Python package installer)

### Installation

1. Clone the repository:
```bash
git clone <your-repo-url>
cd windsurf-project
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment:
```bash
cp .envexample .env
```
Edit `.env` and add your private key:
```
PRIVATE_KEY=your_private_key_here
```

## 📈 Strategy Details

### Base Strategy
- Starting bet: 10% of balance
- Maximum bet: 25% of balance
- Minimum bet: Configurable safety threshold

### Win Streak Strategy
- +20% bet increase per consecutive win
- Capped at 2x the base bet
- Resets on loss

### Loss Recovery
- +15% bet increase per consecutive loss
- Capped at 2x the base bet
- Intelligent bankroll management

### 69 Pattern Chasing
- Activates after 15 games without 69 pattern
- Progressive bet increases (10% per game)
- Capped at 3x multiplier
- Resets on pattern hit

## 📝 Configuration

Key settings in `config.py`:
- `SAFETY_THRESHOLD`: Minimum balance to continue betting
- `MIN_BET_AMOUNT`: Minimum bet size
- `MAX_BET_PERCENTAGE`: Maximum bet as percentage of balance

Strategy settings in `bot.py`:
- `min_bet_percentage`: Starting bet size (10%)
- `max_bet_percentage`: Maximum bet size (25%)
- `streak_multiplier`: Win streak bonus (1.2x)
- `chase_69_threshold`: Games before 69 chase (15)
- `chase_69_multiplier`: Chase bonus per game (1.1x)

## 📊 Logging

The bot provides detailed logging:
- Balance updates and performance metrics
- Strategy decisions and multipliers
- Win/Loss tracking with percentages
- Transaction details and gas savings
- 69 pattern drought tracking

## ⚠️ Security

- Never commit your private key
- Use `.env` for sensitive data
- Test with small amounts first
- Monitor the bot's activity regularly
- Keep your environment secure

## ⚖️ Disclaimer

This bot is for educational purposes only. Gambling involves risk. Never bet more than you can afford to lose. Make sure to comply with apes.win terms of service.

## 🤝 Contributing

Contributions welcome! Please read the contributing guidelines before submitting PRs.

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
