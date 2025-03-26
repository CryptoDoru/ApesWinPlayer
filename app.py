import os
import json
import threading
import time
import logging
from datetime import datetime
from flask import Flask, render_template, jsonify, request

# Import our bot
from bot import ApesWinBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('dashboard')

app = Flask(__name__)

# Global variables
bot = ApesWinBot()
bot_thread = None
bot_running = False

# Function to fetch and update balances
def update_balances():
    try:
        # Get banana balance
        raw_banana_balance = bot.contract_manager.get_banana_balance()
        formatted_banana_balance = bot.format_bananas(raw_banana_balance)
        
        # Get S token balance
        raw_s_balance = bot.contract_manager.get_native_balance()
        formatted_s_balance = bot.contract_manager.format_native(raw_s_balance)
        
        # Update stats with balances
        stats['current_balance'] = formatted_banana_balance
        stats['s_token_balance'] = formatted_s_balance
        
        return True
    except Exception as e:
        logger.error(f"Error updating balances: {e}")
        return False
stats = {
    'current_balance': 0,
    'all_time_high': 0,
    'win_streak': 0,
    'loss_streak': 0,
    'games_since_69': 0,
    'total_games': 0,
    'total_wins': 0,
    'total_losses': 0,
    'session_profit': 0,
    'start_balance': 0,
    'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    'log_messages': [],
    'recent_games': []
}

# Custom log handler to capture logs
class DashboardLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.messages = []
        self.max_messages = 100  # Store last 100 messages

    def emit(self, record):
        log_entry = {
            'time': datetime.now().strftime('%H:%M:%S'),
            'level': record.levelname,
            'message': self.format(record)
        }
        self.messages.append(log_entry)
        if len(self.messages) > self.max_messages:
            self.messages.pop(0)
        
        # Update global stats
        stats['log_messages'] = self.messages

# Setup custom log handler
dashboard_handler = DashboardLogHandler()
dashboard_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
dashboard_handler.setFormatter(formatter)

# Add to bot's logger
root_logger = logging.getLogger()
root_logger.addHandler(dashboard_handler)

# Bot thread function
def bot_worker():
    global bot_running, stats
    # Reset session stats
    stats['total_games'] = 0 
    stats['total_wins'] = 0
    stats['total_losses'] = 0
    
    # Get initial balances for session profit tracking
    raw_banana_balance = bot.contract_manager.get_banana_balance()
    formatted_banana_balance = bot.format_bananas(raw_banana_balance)
    
    # Get S token balance
    raw_s_balance = bot.contract_manager.get_native_balance()
    formatted_s_balance = bot.contract_manager.format_native(raw_s_balance)
    
    # Store both raw and formatted balances
    stats['start_balance'] = raw_banana_balance / 10**18 # Convert raw balance to decimal
    stats['current_balance'] = formatted_banana_balance
    stats['s_token_balance'] = formatted_s_balance
    stats['session_profit'] = 0
    
    logger.info(f"🚀 Bot starting with {formatted_banana_balance} 🍌 balance and {formatted_s_balance} S token balance...")
    
    while bot_running:
        try:
            result = bot.play_dice_game()
            
            # Get current banana balance
            raw_banana_balance = bot.contract_manager.get_banana_balance()
            formatted_banana_balance = bot.format_bananas(raw_banana_balance)
            decimal_banana_balance = raw_banana_balance / 10**18
            
            # Get current S token balance
            raw_s_balance = bot.contract_manager.get_native_balance()
            formatted_s_balance = bot.contract_manager.format_native(raw_s_balance)
            
            # Update statistics with properly formatted balances
            stats['current_balance'] = formatted_banana_balance
            stats['s_token_balance'] = formatted_s_balance
            stats['all_time_high'] = bot.format_bananas(bot.all_time_high)
            stats['win_streak'] = bot.win_streak
            stats['loss_streak'] = bot.loss_streak
            stats['games_since_69'] = bot.games_since_69
            stats['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Calculate session profit using decimal balances for accuracy
            stats['session_profit'] = round(decimal_banana_balance - stats['start_balance'], 2)
            
            # Only count games that actually happened (result is not None)
            if result:
                stats['total_games'] += 1
                if 'won' in result and result['won']:
                    stats['total_wins'] += 1
                else:
                    stats['total_losses'] += 1
                
                # Log the current stats for debugging
                logger.info(f"Stats update - Games: {stats['total_games']}, Wins: {stats['total_wins']}, Losses: {stats['total_losses']}")
                
            # Add game to recent games list
            if result:
                # Format game result for display
                game_info = {
                    'game_id': result.get('game_id', 'Unknown'),
                    'time': datetime.now().strftime('%H:%M:%S'),
                    'dice': result.get('dice', []),
                    'won': result.get('won', False),
                    'amount': result.get('bet_amount', 0),
                    'balance_change': result.get('balance_change', 0)
                }
                stats['recent_games'].insert(0, game_info)
                # Keep only last 10 games
                if len(stats['recent_games']) > 10:
                    stats['recent_games'].pop()
            
            # Wait between games
            time.sleep(3)
            
        except Exception as e:
            logger.error(f"Error in bot thread: {e}")
            time.sleep(5)  # Wait a bit before retrying
    
    logger.info("Bot stopped.")

@app.route('/')
def home():
    # Update balances when the home page is loaded
    update_balances()
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    return jsonify(stats)

@app.route('/api/refresh_balances')
def refresh_balances():
    success = update_balances()
    return jsonify({
        'status': 'success' if success else 'error',
        'current_balance': stats['current_balance'],
        's_token_balance': stats['s_token_balance']
    })

@app.route('/api/set_private_key', methods=['POST'])
def set_private_key():
    global bot, stats
    try:
        data = request.json
        private_key = data.get('private_key')
        
        # Validate private key format
        if not private_key or not private_key.startswith('0x') or len(private_key) != 66:
            return jsonify({'status': 'error', 'message': 'Invalid private key format'}), 400
            
        # Update the bot with the new private key
        wallet_address = bot.update_wallet(private_key)
        
        # Update balances
        update_balances()
        
        return jsonify({
            'status': 'success',
            'wallet_address': wallet_address,
            'current_balance': stats['current_balance'],
            's_token_balance': stats['s_token_balance']
        })
    except Exception as e:
        logger.error(f"Error setting private key: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/start', methods=['POST'])
def start_bot():
    global bot_thread, bot_running
    
    if not bot_running:
        bot_running = True
        bot_thread = threading.Thread(target=bot_worker)
        bot_thread.start()
        return jsonify({'status': 'started'})
    
    return jsonify({'status': 'already_running'})

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    global bot_running
    
    if bot_running:
        bot_running = False
        return jsonify({'status': 'stopping'})
    
    return jsonify({'status': 'not_running'})

@app.route('/api/reset_stats', methods=['POST'])
def reset_stats():
    global stats
    
    stats['total_games'] = 0
    stats['total_wins'] = 0
    stats['total_losses'] = 0
    stats['recent_games'] = []
    
    return jsonify({'status': 'stats_reset'})

@app.route('/api/current_settings', methods=['GET'])
def get_settings():
    settings = {
        'min_bet_percentage': bot.min_bet_percentage,
        'max_bet_percentage': bot.max_bet_percentage,
        'loss_recovery_rate': bot.loss_recovery_rate,
        'chase_69_threshold': bot.chase_69_threshold,
        'chase_69_multiplier': bot.chase_69_multiplier
    }
    return jsonify(settings)

# Create required directories
os.makedirs('templates', exist_ok=True)
os.makedirs('static', exist_ok=True)

# For Vercel deployment
app.debug = True  # Set to False in production

if __name__ == '__main__':
    # Only run the app directly when running locally
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5556)
