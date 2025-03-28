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
    
    # If bot exists for this user
    if user_id in user_bots and user_bots[user_id] is not None:
        # If private key is provided and different from current one, update it
        if private_key and (not user_bots[user_id].contract_manager.private_key or 
                           private_key != user_bots[user_id].contract_manager.private_key):
            try:
                # Update existing bot with new private key
                wallet_address = user_bots[user_id].contract_manager.update_private_key(private_key)
                logger.info(f"Updated private key for existing bot for user {user_id[:8]}... Address: {wallet_address}")
            except Exception as e:
                logger.error(f"Error updating private key for user {user_id[:8]}...: {e}")
        return user_bots[user_id]
    
    # Create new bot instance
    try:
        user_bots[user_id] = ApesWinBot(private_key)
        logger.info(f"Created new bot for user {user_id[:8]}...")
        
        # If private key was provided, verify wallet connection
        if private_key and user_bots[user_id].contract_manager.account:
            address = user_bots[user_id].contract_manager.account.address
            logger.info(f"New bot created with wallet connected: {address}")
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
        
        # Add a small delay to ensure contract calls are ready
        time.sleep(0.1)
        
        try:
            # Get banana balance with error handling
            raw_banana_balance = current_bot.contract_manager.get_banana_balance()
            # Use the improved format_bananas method with 2 decimal places for dashboard display
            formatted_banana_balance = current_bot.format_bananas(raw_banana_balance, decimal_places=2)
        except Exception as e:
            logger.error(f"Error getting banana balance: {e}")
            formatted_banana_balance = user_stats[user_id].get('current_balance', "0.00")
        
        try:
            # Get S token balance with error handling
            raw_s_balance = current_bot.contract_manager.get_native_balance()
            
            # Use the contract manager's format_native method to correctly format S token balance
            if isinstance(raw_s_balance, (int, float)):
                s_token_value = current_bot.contract_manager.format_native(raw_s_balance)
                formatted_s_balance = f"{s_token_value:.2f}"  # Limit S token to 2 decimal places
            else:
                formatted_s_balance = "0.00"
        except Exception as e:
            logger.error(f"Error getting S token balance: {e}")
            formatted_s_balance = user_stats[user_id].get('s_token_balance', "0.00")
        
        # Add current bet amount if the bot is running
        # First check for current_bet_amount (actual bet with modifiers), then fallback to base_bet_amount
        if hasattr(current_bot, 'current_bet_amount') and current_bot.current_bet_amount is not None:
            try:
                # Format the actual current bet amount with limited decimal places
                current_bet = current_bot.format_bananas(current_bot.current_bet_amount, decimal_places=2)
                user_stats[user_id]['current_bet'] = current_bet
            except Exception as e:
                logger.error(f"Error getting current bet: {e}")
                user_stats[user_id]['current_bet'] = "0.00"
        elif hasattr(current_bot, 'base_bet_amount') and current_bot.base_bet_amount is not None:
            try:
                # Fall back to base bet amount if actual bet isn't set yet
                current_bet = current_bot.format_bananas(current_bot.base_bet_amount, decimal_places=2)
                user_stats[user_id]['current_bet'] = current_bet
            except Exception as e:
                logger.error(f"Error getting base bet: {e}")
                user_stats[user_id]['current_bet'] = "0.00"
        else:
            user_stats[user_id]['current_bet'] = "0.00"
            
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
    
    # Store reference to user ID in bot for stopping checks
    current_bot._user_id = user_id
    current_bot._should_stop = False  # Initialize stop flag
    
    # Get initial balances for session profit tracking
    raw_banana_balance = current_bot.contract_manager.get_banana_balance()
    formatted_banana_balance = current_bot.format_bananas(raw_banana_balance)
    
    # Get S token balance
    raw_s_balance = current_bot.contract_manager.get_native_balance()
    formatted_s_balance = f"{current_bot.contract_manager.format_native(raw_s_balance):.2f}"  # Limit to 2 decimal places
    
    # Store both raw and formatted balances
    decimal_balance = raw_banana_balance / 10**18 # Convert raw balance to decimal
    user_stats[user_id]['start_balance'] = decimal_balance
    user_stats[user_id]['current_balance'] = formatted_banana_balance
    user_stats[user_id]['s_token_balance'] = formatted_s_balance
    user_stats[user_id]['session_profit'] = 0
    
    # Set session start balance in the bot instance
    current_bot.session_start_balance = decimal_balance
    
    logger.info(f"🚀 Bot starting for user {user_id[:8]}... with {formatted_banana_balance} 🍌 balance and {formatted_s_balance} S token balance...")
    
    while user_id in user_running and user_running[user_id] and not current_bot._should_stop:
        try:
            # Check if we should stop before making a transaction
            if not user_id in user_running or not user_running[user_id] or current_bot._should_stop:
                logger.info(f"⛔️ Bot stopping before transaction for user {user_id[:8]}...")
                break
                
            # Get current bot instance
            current_bot = get_bot(user_id=user_id)
            # Pass user_id to bot for reference
            current_bot._user_id = user_id
            # Make sure we pass the stop flag to the bot
            current_bot._should_stop = not (user_id in user_running and user_running[user_id])
            
            # Only proceed with bet if we're still supposed to be running
            if current_bot._should_stop:
                logger.info(f"⛔️ Bot detected stop signal, halting transactions for user {user_id[:8]}...")
                break
                
            # Create log capture handler to intercept specific log messages
            class CurrentBetLogger(logging.Handler):
                def emit(self, record):
                    if "CURRENT_BET_SET:" in record.getMessage():
                        try:
                            # Extract the bet amount from the log message
                            msg = record.getMessage()
                            bet_amount = msg.split("CURRENT_BET_SET:")[1].split(" 🍌")[0].strip()
                            user_stats[user_id]['current_bet'] = bet_amount
                            logger.info(f"Updated dashboard with current bet: {bet_amount} 🍌")
                        except Exception as e:
                            logger.error(f"Error parsing bet amount: {e}")
            
            # Add the custom handler to root logger
            bet_logger = CurrentBetLogger()
            logging.getLogger().addHandler(bet_logger)
            
            # Execute the dice game
            result = current_bot.play_dice_game()
            
            # Remove the temporary logger to avoid memory leaks
            logging.getLogger().removeHandler(bet_logger)
            
            # Get current banana balance
            raw_banana_balance = current_bot.contract_manager.get_banana_balance()
            formatted_banana_balance = current_bot.format_bananas(raw_banana_balance)
            decimal_banana_balance = raw_banana_balance / 10**18
            
            # Get current S token balance
            raw_s_balance = current_bot.contract_manager.get_native_balance()
            formatted_s_balance = f"{current_bot.contract_manager.format_native(raw_s_balance):.2f}"  # Limit to 2 decimal places
            
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
            
            # Check if we should stop before waiting
            if not user_id in user_running or not user_running[user_id] or current_bot._should_stop:
                logger.info(f"⛔️ Bot stopping during wait cycle for user {user_id[:8]}...")
                break
                
            # Wait between games with periodic stop checks
            # Break the wait into smaller chunks so we can check for stop signals more frequently
            for _ in range(6):  # 6 x 0.5s = 3s total wait time
                if not user_id in user_running or not user_running[user_id] or current_bot._should_stop:
                    logger.info(f"⛔️ Bot stopping during wait cycle for user {user_id[:8]}...")
                    break
                time.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error in bot thread for user {user_id[:8]}...: {e}")
            # Add a full traceback for better debugging
            import traceback
            logger.error(f"Detailed traceback:\n{traceback.format_exc()}")
            
            # Update user stats to show error
            if user_id in user_stats:
                user_stats[user_id]['status'] = 'error'
                user_stats[user_id]['error'] = str(e)
                
            # Wait a bit before retrying, but check for stop signal first
            for _ in range(10):  # 10 x 0.5s = 5s total wait time
                if not user_id in user_running or not user_running[user_id] or current_bot._should_stop:
                    logger.info(f"⛔️ Bot stopping during error recovery for user {user_id[:8]}...")
                    break
                time.sleep(0.5)
    
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
    stats = get_user_stats()
    
    # Check if user has a bot with a connected wallet
    if user_id in user_bots and user_bots[user_id].contract_manager.private_key:
        # Add wallet connection status and address
        stats['wallet_connected'] = True
        stats['wallet_address'] = user_bots[user_id].contract_manager.account.address
    else:
        stats['wallet_connected'] = False
        stats['wallet_address'] = None
        
    return jsonify(stats)

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
        
        # Get bot instance for this user first without setting private key
        current_bot = get_bot(user_id=user_id)
        
        # Update the wallet with the new private key
        try:
            wallet_address = current_bot.contract_manager.update_private_key(private_key)
            logger.info(f"Wallet address updated: {wallet_address}")
        except ValueError as e:
            logger.error(f"Private key validation error: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 400
        
        # Make sure user stats exists
        if user_id not in user_stats:
            user_stats[user_id] = get_default_stats()
        
        # Update balances with retry
        retries = 2
        success = False
        
        while retries > 0 and not success:
            success = update_balances(user_id)
            if not success:
                logger.warning(f"Retrying balance update ({retries} attempts left)")
                time.sleep(0.5)  # Short delay before retry
                retries -= 1
        
        if not success:
            logger.error(f"Failed to update balances after multiple attempts for user {user_id[:8]}")
        
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
        logger.info(f"⛔️ Stopping bot for user {user_id[:8]}...")
        # Set global flag to stop the bot worker thread
        user_running[user_id] = False
        
        # Also set the bot instance flag to ensure it stops mid-execution
        if user_id in user_bots and user_bots[user_id] is not None:
            user_bots[user_id]._should_stop = True
            logger.info("Setting bot's internal stop flag to prevent new transactions")
            
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
        'win_streak_rate': current_bot.win_streak_rate,
        'loss_recovery_rate': current_bot.loss_recovery_rate,
        'chase_69_threshold': current_bot.chase_69_threshold,
        'chase_69_multiplier': current_bot.chase_69_multiplier,
        'win_sensitivity': getattr(current_bot, 'win_sensitivity', 0.5),
        'loss_sensitivity': getattr(current_bot, 'loss_sensitivity', 0.5),
        'max_track_games': getattr(current_bot, 'max_track_games', 20)
    }
    return jsonify(settings)

# Route to save new bot settings
@app.route('/api/save_settings', methods=['POST'])
def save_settings():
    user_id = get_user_id()
    current_bot = get_bot(user_id=user_id)
    
    try:
        # Get settings from request json
        settings = request.get_json()
        
        # Validate settings
        if settings['min_bet_percentage'] >= settings['max_bet_percentage']:
            return jsonify({
                'status': 'error',
                'message': 'Minimum bet percentage must be less than maximum bet percentage'
            })
            
        if settings['min_bet_percentage'] < 0.01 or settings['max_bet_percentage'] > 0.5:
            return jsonify({
                'status': 'error',
                'message': 'Bet percentages must be between 1% and 50%'
            })
        
        # Update bot settings
        current_bot.min_bet_percentage = float(settings['min_bet_percentage'])
        current_bot.max_bet_percentage = float(settings['max_bet_percentage'])
        current_bot.win_streak_rate = float(settings['win_streak_rate'])
        current_bot.loss_recovery_rate = float(settings['loss_recovery_rate'])
        current_bot.chase_69_threshold = int(settings['chase_69_threshold'])
        current_bot.chase_69_multiplier = float(settings['chase_69_multiplier'])
        
        # Update advanced strategy parameters if provided
        if 'win_sensitivity' in settings:
            current_bot.win_sensitivity = float(settings['win_sensitivity'])
        if 'loss_sensitivity' in settings:
            current_bot.loss_sensitivity = float(settings['loss_sensitivity'])
        if 'max_track_games' in settings:
            current_bot.max_track_games = int(settings['max_track_games'])
        
        logger.info(f"Bot settings updated for user {user_id[:8]}...")
        return jsonify({'status': 'success'})
        
    except Exception as e:
        logger.error(f"Error saving settings for user {user_id[:8]}...: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        })

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
