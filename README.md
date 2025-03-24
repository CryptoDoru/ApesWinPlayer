# Apes.win Bot

A Python bot for automating interactions with the apes.win game on the Sonic blockchain. The bot handles crate claiming, COIN to Banana conversion, and dice game betting using a conservative strategy.

## Features

- Automatic crate claiming every 6 hours
- COIN to Banana conversion when threshold is met
- Dice game betting with 10% balance strategy
- Risk management with consecutive loss handling
- Safety thresholds to prevent balance depletion

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your private key:
```
PRIVATE_KEY=your_private_key_here
```

3. Update `config.py` with:
- Contract ABIs
- Missing contract addresses
- RPC URL verification

## Usage

Run the bot:
```bash
python bot.py
```

## Configuration

Key parameters in `config.py`:
- `MAX_BET_PERCENTAGE`: Percentage of balance to bet (default: 10%)
- `SAFETY_THRESHOLD`: Minimum balance to maintain
- `CRATE_CLAIM_INTERVAL`: Time between crate claims
- `DICE_ROLL_INTERVAL`: Time between dice rolls

## Important Note

Before running the bot, we need:
1. Complete contract ABIs
2. Missing contract addresses
3. Verification of RPC endpoint
4. Proper private key configuration

## Security

- Never share your private key
- Test with small amounts first
- Monitor the bot's activity regularly
- Keep your environment secure

## Disclaimer

This bot is provided as-is. Use at your own risk. Make sure to comply with apes.win terms of service.
