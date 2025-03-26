import os
import json
import threading
import time
import logging
import os
import uuid
from datetime import datetime
from flask import Flask, render_template, jsonify, request, session

# Import our bot
from bot import ApesWinBot

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('dashboard')

app = Flask(__name__)

# Configure secure sessions
app.secret_key = os.environ.get('FLASK_SECRET_KEY', os.urandom(24).hex())
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = False
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours

# Enable CORS for Vercel serverless environment
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Cookie, Set-Cookie'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

# Handle OPTIONS requests (for CORS preflight)
@app.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@app.route('/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    return '', 204

# Dictionary to store user-specific bots and threads
user_bots = {}
user_threads = {}
user_running = {}

# Function to get user's session ID
def get_user_id():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())
    return session['user_id']

# Function to get bot for specific user
def get_bot(private_key=None, user_id=None):
    if not user_id:
        user_id = get_user_id()
        
    if user_id not in user_bots or user_bots[user_id] is None:
        try:
            user_bots[user_id] = ApesWinBot(private_key)
            logger.info(f"Created new bot for user {user_id[:8]}...")
        except Exception as e:
            logger.error(f"Error initializing bot for user {user_id[:8]}...: {e}")
            # Create with minimum functionality
            user_bots[user_id] = ApesWinBot()
    return user_bots[user_id]

# Default stats template
def get_default_stats():
    return {
        'current_balance': 0,
        'all_time_high': 0,
        'win_streak': 0,
        'loss_streak': 0,
        'games_since_69': 0,
        'total_games': 0,
        'total_wins': 0,
        'total_losses': 0,
        'session_profit': 0,
        's_token_balance': 0,
        'start_balance': 0,
        'recent_games': [],
        'log_messages': [],
        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

# Get user-specific stats
def get_user_stats():
    user_id = get_user_id()
    if user_id not in user_stats:
        user_stats[user_id] = get_default_stats()
    return user_stats[user_id]

# Function to fetch and update balances
def update_balances(user_id=None):
    if not user_id:
        user_id = get_user_id()
        
    # Initialize user stats if needed
    if user_id not in user_stats:
        user_stats[user_id] = get_default_stats()
        
    try:
        # Get current bot instance or initialize it
        current_bot = get_bot(user_id=user_id)
        
        # Check if wallet is connected (has private key)
        if not current_bot.contract_manager.private_key:
            # No wallet connected yet
            user_stats[user_id]['current_balance'] = "0.00"
            user_stats[user_id]['s_token_balance'] = "0.00"
            user_stats[user_id]['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"No wallet connected for user {user_id[:8]}...")
            return False
        
        # Get banana balance
        raw_banana_balance = current_bot.contract_manager.get_banana_balance()
        formatted_banana_balance = current_bot.format_bananas(raw_banana_balance)
        
        # Get S token balance
        raw_s_balance = current_bot.contract_manager.get_native_balance()
        formatted_s_balance = current_bot.contract_manager.format_native(raw_s_balance)
        
        # Update user-specific stats with balances
        user_stats[user_id]['current_balance'] = formatted_banana_balance
        user_stats[user_id]['s_token_balance'] = formatted_s_balance
        user_stats[user_id]['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        logger.info(f"Updated balances for user {user_id[:8]}... BANANA: {formatted_banana_balance}, S-TOKEN: {formatted_s_balance}")
        return True
    except Exception as e:
        logger.error(f"Error updating balances for user {user_id[:8]}...: {e}")
        return False

# Dictionary to store user-specific stats
user_stats = {}

# Custom log handler to capture logs
class DashboardLogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.user_messages = {}  # Dictionary to store user-specific messages
        self.max_messages = 100  # Store last 100 messages per user

    def emit(self, record):
        # Parse user_id from the log message if present
        message = self.format(record)
        user_id = None
        
        # Try to extract user ID from log messages that include it
        if 'for user' in message:
            try:
                user_id_part = message.split('for user ')[1].split('...')[0]
                user_id = user_id_part + '...'  # Just the truncated ID
            except:
                pass
        
        log_entry = {
            'time': datetime.now().strftime('%H:%M:%S'),
            'level': record.levelname,
            'message': message
        }
        
        # If we have active sessions, add log to the appropriate user's logs
        if user_id and user_id in user_stats:
            if user_id not in self.user_messages:
                self.user_messages[user_id] = []
            
            self.user_messages[user_id].append(log_entry)
            if len(self.user_messages[user_id]) > self.max_messages:
                self.user_messages[user_id].pop(0)
                
            # Update user-specific stats with logs
            user_stats[user_id]['log_messages'] = self.user_messages[user_id]
        else:
            # For general logs or logs without user_id, add to all active sessions
            for active_user_id in user_stats:
                if active_user_id not in self.user_messages:
                    self.user_messages[active_user_id] = []
                
                self.user_messages[active_user_id].append(log_entry)
                if len(self.user_messages[active_user_id]) > self.max_messages:
                    self.user_messages[active_user_id].pop(0)
                    
                # Update user-specific stats
                user_stats[active_user_id]['log_messages'] = self.user_messages[active_user_id]

# Setup custom log handler
dashboard_handler = DashboardLogHandler()
dashboard_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
dashboard_handler.setFormatter(formatter)

# Add to bot's logger
root_logger = logging.getLogger()
root_logger.addHandler(dashboard_handler)

# Bot thread function
def bot_worker(user_id=None):
    if not user_id:
        user_id = get_user_id()
    
    # Reset session stats
    user_stats[user_id] = get_default_stats()
    
    # Get bot instance (initialize if needed)
    current_bot = get_bot(user_id=user_id)
    
    # Get initial balances for session profit tracking
    raw_banana_balance = current_bot.contract_manager.get_banana_balance()
    formatted_banana_balance = current_bot.format_bananas(raw_banana_balance)
    
    # Get S token balance
    raw_s_balance = current_bot.contract_manager.get_native_balance()
    formatted_s_balance = current_bot.contract_manager.format_native(raw_s_balance)
    
    # Store both raw and formatted balances
    decimal_balance = raw_banana_balance / 10**18 # Convert raw balance to decimal
    user_stats[user_id]['start_balance'] = decimal_balance
    user_stats[user_id]['current_balance'] = formatted_banana_balance
    user_stats[user_id]['s_token_balance'] = formatted_s_balance
    user_stats[user_id]['session_profit'] = 0
    
    # Set session start balance in the bot instance
    current_bot.session_start_balance = decimal_balance
    
    logger.info(f"🚀 Bot starting for user {user_id[:8]}... with {formatted_banana_balance} 🍌 balance and {formatted_s_balance} S token balance...")
    
    while user_id in user_running and user_running[user_id]:
        try:
            # Get current bot instance
            current_bot = get_bot(user_id=user_id)
            result = current_bot.play_dice_game()
            
            # Get current banana balance
            raw_banana_balance = current_bot.contract_manager.get_banana_balance()
            formatted_banana_balance = current_bot.format_bananas(raw_banana_balance)
            decimal_banana_balance = raw_banana_balance / 10**18
            
            # Get current S token balance
            raw_s_balance = current_bot.contract_manager.get_native_balance()
            formatted_s_balance = current_bot.contract_manager.format_native(raw_s_balance)
            
            # Update statistics with properly formatted balances
            user_stats[user_id]['current_balance'] = formatted_banana_balance
            user_stats[user_id]['s_token_balance'] = formatted_s_balance
            user_stats[user_id]['all_time_high'] = current_bot.format_bananas(current_bot.all_time_high)
            user_stats[user_id]['win_streak'] = current_bot.win_streak
            user_stats[user_id]['loss_streak'] = current_bot.loss_streak
            user_stats[user_id]['games_since_69'] = current_bot.games_since_69
            user_stats[user_id]['last_update'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            # Calculate session profit using decimal balances for accuracy
            user_stats[user_id]['session_profit'] = round(decimal_banana_balance - user_stats[user_id]['start_balance'], 2)
            
            # Only count games that actually happened (result is not None)
            if result:
                user_stats[user_id]['total_games'] += 1
                if 'won' in result and result['won']:
                    user_stats[user_id]['total_wins'] += 1
                else:
                    user_stats[user_id]['total_losses'] += 1
                
                # Log the current stats for debugging
                logger.info(f"Stats update for user {user_id[:8]}... - Games: {user_stats[user_id]['total_games']}, Wins: {user_stats[user_id]['total_wins']}, Losses: {user_stats[user_id]['total_losses']}")
                
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
                user_stats[user_id]['recent_games'].insert(0, game_info)
                # Keep only last 10 games
                if len(user_stats[user_id]['recent_games']) > 10:
                    user_stats[user_id]['recent_games'].pop()
            
            # Wait between games
            time.sleep(3)
            
        except Exception as e:
            logger.error(f"Error in bot thread for user {user_id[:8]}...: {e}")
            time.sleep(5)  # Wait a bit before retrying
    
    logger.info(f"Bot stopped for user {user_id[:8]}...")
    # Clean up session resources when bot stops
    if user_id in user_running:
        user_running[user_id] = False

@app.route('/')
def home():
    # Create a session ID if needed and update balances
    user_id = get_user_id()
    update_balances(user_id)
    return render_template('index.html')

@app.route('/api/stats')
def get_stats():
    # Get user-specific stats
    user_id = get_user_id()
    return jsonify(get_user_stats())

@app.route('/api/refresh_balances')
def refresh_balances():
    user_id = get_user_id()
    success = update_balances(user_id)
    user_stats = get_user_stats()
    return jsonify({
        'status': 'success' if success else 'error',
        'current_balance': user_stats['current_balance'],
        's_token_balance': user_stats['s_token_balance']
    })

@app.route('/api/set_private_key', methods=['POST'])
def set_private_key():
    try:
        data = request.json
        private_key = data.get('private_key')
        user_id = get_user_id()
        
        # Validate private key format
        if not private_key or not private_key.startswith('0x') or len(private_key) != 66:
            return jsonify({'status': 'error', 'message': 'Invalid private key format'}), 400
        
        # Initialize or update the bot with the new private key
        current_bot = get_bot(private_key, user_id)
        wallet_address = current_bot.update_wallet(private_key)
        
        # Make sure user stats exists
        if user_id not in user_stats:
            user_stats[user_id] = get_default_stats()
        
        # Update balances
        success = update_balances(user_id)
        if not success:
            logger.error(f"Failed to update balances after setting private key for user {user_id[:8]}")
        
        # Log the connected wallet
        logger.info(f"Wallet connected for user {user_id[:8]}... Address: {wallet_address}")
        
        return jsonify({
            'status': 'success',
            'wallet_address': wallet_address,
            'current_balance': user_stats[user_id]['current_balance'],
            's_token_balance': user_stats[user_id]['s_token_balance']
        })
    except Exception as e:
        logger.error(f"Error setting private key: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/start', methods=['POST'])
def start_bot():
    user_id = get_user_id()
    
    if user_id not in user_running or not user_running[user_id]:
        user_running[user_id] = True
        user_threads[user_id] = threading.Thread(target=lambda: bot_worker(user_id))
        user_threads[user_id].start()
        return jsonify({'status': 'started'})
    
    return jsonify({'status': 'already_running'})

@app.route('/api/stop', methods=['POST'])
def stop_bot():
    user_id = get_user_id()
    
    if user_id in user_running and user_running[user_id]:
        user_running[user_id] = False
        return jsonify({'status': 'stopping'})
    
    return jsonify({'status': 'not_running'})

@app.route('/api/reset_stats', methods=['POST'])
def reset_stats():
    user_id = get_user_id()
    user_stats[user_id] = get_default_stats()
    
    return jsonify({'status': 'stats_reset'})

@app.route('/api/current_settings', methods=['GET'])
def get_settings():
    user_id = get_user_id()
    current_bot = get_bot(user_id=user_id)
    
    settings = {
        'min_bet_percentage': current_bot.min_bet_percentage,
        'max_bet_percentage': current_bot.max_bet_percentage,
        'loss_recovery_rate': current_bot.loss_recovery_rate,
        'chase_69_threshold': current_bot.chase_69_threshold,
        'chase_69_multiplier': current_bot.chase_69_multiplier
    }
    return jsonify(settings)

# Create directories if running locally
try:
    # This might fail in read-only Vercel environment, but we don't need it there
    os.makedirs('templates', exist_ok=True)
    os.makedirs('static', exist_ok=True)
except Exception as e:
    print(f"Note: Couldn't create directories, but this is normal in serverless: {e}")

# For Vercel deployment - serverless compatible mode
app.debug = False  # Set to False in production

if __name__ == '__main__':
    # Only run the app directly when running locally
    app.run(debug=True, use_reloader=False, host='0.0.0.0', port=5556)
