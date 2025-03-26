// DOM Elements
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const resetStatsBtn = document.getElementById('resetStatsBtn');
const clearLogsBtn = document.getElementById('clearLogsBtn');
const autoScrollBtn = document.getElementById('autoScrollBtn');
const logMessages = document.getElementById('logMessages');
const recentGames = document.getElementById('recentGames');

// Wallet elements
const privateKeyInput = document.getElementById('privateKeyInput');
const connectWalletBtn = document.getElementById('connectWalletBtn');
const disconnectWalletBtn = document.getElementById('disconnectWalletBtn');
const walletDisconnectedView = document.getElementById('wallet-disconnected-view');
const walletConnectedView = document.getElementById('wallet-connected-view');
const connectedAddress = document.getElementById('connected-address');

// Global wallet state
let walletConnected = false;

// Stats elements
const currentBalance = document.getElementById('currentBalance');
const sTokenBalance = document.getElementById('sTokenBalance');
const refreshBalanceBtn = document.getElementById('refreshBalanceBtn');
const winStreak = document.getElementById('winStreak');
const lossStreak = document.getElementById('lossStreak');
const gamesSince69 = document.getElementById('gamesSince69');
const totalGames = document.getElementById('totalGames');
const totalWins = document.getElementById('totalWins');
const totalLosses = document.getElementById('totalLosses');
const winRate = document.getElementById('winRate');
const lastUpdate = document.getElementById('lastUpdate');
const allTimeHigh = document.getElementById('allTimeHigh');
const sessionProfit = document.getElementById('sessionProfit');

// Settings elements
const minBet = document.getElementById('minBet');
const maxBet = document.getElementById('maxBet');
const lossRecovery = document.getElementById('lossRecovery');
const chaseThreshold = document.getElementById('chaseThreshold');
const chaseMultiplier = document.getElementById('chaseMultiplier');

// State
let autoScroll = true;
let botRunning = false;

// Functions
function updateStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            // Update balances with icons
            currentBalance.textContent = `${data.current_balance} 🍌`;
            sTokenBalance.textContent = `${data.s_token_balance} S`;
            
            // Update streak stats
            winStreak.textContent = data.win_streak;
            lossStreak.textContent = data.loss_streak;
            gamesSince69.textContent = data.games_since_69;
            
            // Ensure performance metrics update properly
            totalGames.textContent = data.total_games;
            totalWins.textContent = data.total_wins;
            totalLosses.textContent = data.total_losses;
            
            // Display session profit with color coding
            const profit = data.session_profit;
            sessionProfit.textContent = profit > 0 ? `+${profit}` : profit;
            sessionProfit.style.color = profit > 0 ? 'green' : profit < 0 ? 'red' : 'inherit';
            
            // Calculate win rate
            const calculatedWinRate = data.total_games > 0 
                ? ((data.total_wins / data.total_games) * 100).toFixed(1)
                : 0;
            winRate.textContent = `${calculatedWinRate}%`;
            
            lastUpdate.textContent = data.last_update;
            allTimeHigh.textContent = data.all_time_high;
            
            // Update log messages
            updateLogs(data.log_messages);
            
            // Update recent games
            updateRecentGames(data.recent_games);
        })
        .catch(error => console.error('Error fetching stats:', error));
}

function updateLogs(messages) {
    if (!messages || messages.length === 0) return;
    
    // Clear existing logs if we have too many
    if (logMessages.children.length > 500) {
        logMessages.innerHTML = '';
    }
    
    // Get the last message we have
    const lastMsg = logMessages.lastElementChild ? 
        logMessages.lastElementChild.querySelector('.log-text').textContent : '';
    
    // Add new messages
    let newMessagesAdded = false;
    for (const msg of messages) {
        // Skip if message is already in the log
        if (logMessages.textContent.includes(msg.message)) continue;
        
        const logEntry = document.createElement('div');
        logEntry.className = 'log-entry';
        
        const timeSpan = document.createElement('span');
        timeSpan.className = 'log-time';
        timeSpan.textContent = msg.time;
        
        const levelSpan = document.createElement('span');
        levelSpan.className = `log-level ${msg.level.toLowerCase()}`;
        levelSpan.textContent = msg.level;
        
        const textSpan = document.createElement('span');
        textSpan.className = 'log-text';
        textSpan.textContent = msg.message;
        
        logEntry.appendChild(timeSpan);
        logEntry.appendChild(levelSpan);
        logEntry.appendChild(textSpan);
        
        logMessages.appendChild(logEntry);
        newMessagesAdded = true;
    }
    
    // Auto-scroll to bottom
    if (autoScroll && newMessagesAdded) {
        logMessages.scrollTop = logMessages.scrollHeight;
    }
}

function updateRecentGames(games) {
    if (!games || games.length === 0) {
        recentGames.innerHTML = '<div class="loading-message">No games played yet</div>';
        return;
    }
    
    recentGames.innerHTML = '';
    
    for (const game of games) {
        const gameItem = document.createElement('div');
        gameItem.className = 'game-item';
        
        // Add special highlight for 69 pattern wins
        if (game.is_69) {
            gameItem.classList.add('pattern-69');
        }
        
        // Left side - time, game ID, dice
        const gameLeft = document.createElement('div');
        gameLeft.className = 'game-left';
        
        const gameTime = document.createElement('div');
        gameTime.className = 'game-time';
        gameTime.textContent = game.time;
        
        const gameId = document.createElement('div');
        gameId.className = 'game-id';
        gameId.textContent = `#${game.game_id}`;
        
        const diceResult = document.createElement('div');
        diceResult.className = 'dice-result';
        
        // Create dice with improved styling
        if (game.dice && game.dice.length) {
            game.dice.forEach(die => {
                const diceElement = document.createElement('div');
                diceElement.className = 'dice';
                // Different background colors for different dice values
                diceElement.classList.add(`dice-${die}`);
                diceElement.textContent = die;
                diceResult.appendChild(diceElement);
            });
        }
        
        gameLeft.appendChild(gameTime);
        gameLeft.appendChild(gameId);
        gameLeft.appendChild(diceResult);
        
        // Right side - amount, result and balance change
        const gameRight = document.createElement('div');
        gameRight.className = 'game-right';
        
        const gameAmount = document.createElement('div');
        gameAmount.className = 'game-amount';
        gameAmount.textContent = formatAmount(game.amount);
        
        // Add balance change info
        const balanceChange = document.createElement('div');
        balanceChange.className = `balance-change ${game.won ? 'positive' : 'negative'}`;
        balanceChange.textContent = game.won 
            ? `+${game.balance_change}` 
            : `-${game.balance_change}`;
        
        const gameResult = document.createElement('div');
        gameResult.className = `game-result ${game.won ? 'win' : 'loss'}`;
        
        // Add 69 pattern indicator if applicable
        if (game.is_69) {
            gameResult.textContent = game.won ? '69 WIN 🌟' : 'LOSS';
            gameResult.classList.add('pattern-result');
        } else {
            gameResult.textContent = game.won ? 'WIN' : 'LOSS';
        }
        
        gameRight.appendChild(gameAmount);
        gameRight.appendChild(balanceChange);
        gameRight.appendChild(gameResult);
        
        // Add to game item
        gameItem.appendChild(gameLeft);
        gameItem.appendChild(gameRight);
        
        recentGames.appendChild(gameItem);
    }
}

function formatAmount(amount) {
    // Format bet amount 
    return `${amount} 🍌`;
}

function fetchSettings() {
    fetch('/api/current_settings')
        .then(response => response.json())
        .then(data => {
            minBet.textContent = `${(data.min_bet_percentage * 100).toFixed(0)}%`;
            maxBet.textContent = `${(data.max_bet_percentage * 100).toFixed(0)}%`;
            lossRecovery.textContent = `${(data.loss_recovery_rate * 100).toFixed(0)}%`;
            chaseThreshold.textContent = data.chase_69_threshold;
            chaseMultiplier.textContent = `${data.chase_69_multiplier}x`;
        })
        .catch(error => console.error('Error fetching settings:', error));
}

// Event Listeners
startBtn.addEventListener('click', () => {
    fetch('/api/start', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'started' || data.status === 'already_running') {
                botRunning = true;
                startBtn.disabled = true;
                stopBtn.disabled = false;
            }
        })
        .catch(error => console.error('Error starting bot:', error));
});

stopBtn.addEventListener('click', () => {
    fetch('/api/stop', { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'stopping') {
                botRunning = false;
                startBtn.disabled = false;
                stopBtn.disabled = true;
            }
        })
        .catch(error => console.error('Error stopping bot:', error));
});

resetStatsBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to reset all statistics?')) {
        fetch('/api/reset_stats', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'stats_reset') {
                    updateStats();
                }
            })
            .catch(error => console.error('Error resetting stats:', error));
    }
});

clearLogsBtn.addEventListener('click', () => {
    logMessages.innerHTML = '';
});

autoScrollBtn.addEventListener('click', () => {
    autoScroll = !autoScroll;
    autoScrollBtn.classList.toggle('btn-active', autoScroll);
});

// Prevent scrolling from disabling auto-scroll
logMessages.addEventListener('wheel', () => {
    // Check if user scrolled to bottom
    const isAtBottom = logMessages.scrollHeight - logMessages.clientHeight <= logMessages.scrollTop + 10;
    
    // Only turn off auto-scroll if user scrolls up while auto-scroll is enabled
    if (autoScroll && !isAtBottom) {
        autoScroll = false;
        autoScrollBtn.classList.remove('btn-active');
    }
});

// Refresh balances button
refreshBalanceBtn.addEventListener('click', () => {
    // Add a spinning animation to the refresh icon
    const refreshIcon = refreshBalanceBtn.querySelector('i');
    refreshIcon.classList.add('fa-spin');
    refreshBalanceBtn.disabled = true;
    
    // Call the refresh balances API
    fetch('/api/refresh_balances')
        .then(response => response.json())
        .then(data => {
            // Update the balance displays
            if (data.status === 'success') {
                currentBalance.textContent = `${data.current_balance} 🍌`;
                sTokenBalance.textContent = `${data.s_token_balance} S`;
            }
        })
        .catch(error => console.error('Error refreshing balances:', error))
        .finally(() => {
            // Stop the spinning animation
            setTimeout(() => {
                refreshIcon.classList.remove('fa-spin');
                refreshBalanceBtn.disabled = false;
            }, 500);
        });
});

// Wallet Connection Logic
connectWalletBtn.addEventListener('click', () => {
    const privateKey = privateKeyInput.value.trim();
    
    // Basic validation
    if (!privateKey || !privateKey.startsWith('0x') || privateKey.length !== 66) {
        alert('Please enter a valid private key (0x followed by 64 hexadecimal characters)');
        return;
    }
    
    // Disable button and show loading state
    connectWalletBtn.disabled = true;
    connectWalletBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Connecting...';
    
    // Send to server
    fetch('/api/set_private_key', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ private_key: privateKey })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Update UI to show connected state
            walletConnected = true;
            walletDisconnectedView.style.display = 'none';
            walletConnectedView.style.display = 'block';
            
            // Display wallet address with truncation
            const address = data.wallet_address;
            const truncatedAddress = `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
            connectedAddress.textContent = truncatedAddress;
            connectedAddress.title = address; // Full address on hover
            
            // Update balances
            currentBalance.textContent = `${data.current_balance} 🍌`;
            sTokenBalance.textContent = `${data.s_token_balance} S`;
            
            // Store the private key in session storage (not local storage for security)
            // This allows reconnection if page is refreshed
            sessionStorage.setItem('dice_bot_pk', privateKey);
            
            // Enable start button if it was disabled
            startBtn.disabled = false;
            
            // Clear the input for security
            privateKeyInput.value = '';
        } else {
            // Show error
            alert('Error connecting wallet: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error setting private key:', error);
        alert('Failed to connect wallet. Please try again.');
    })
    .finally(() => {
        // Reset button state
        connectWalletBtn.disabled = false;
        connectWalletBtn.innerHTML = 'Connect Wallet';
    });
});

// Wallet Disconnection
disconnectWalletBtn.addEventListener('click', () => {
    // Remove private key from session storage
    sessionStorage.removeItem('dice_bot_pk');
    
    // Update UI
    walletConnected = false;
    walletConnectedView.style.display = 'none';
    walletDisconnectedView.style.display = 'block';
    
    // Disable bot controls if running
    if (botRunning) {
        fetch('/api/stop', { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                botRunning = false;
                startBtn.disabled = true;
                stopBtn.disabled = true;
            })
            .catch(error => console.error('Error stopping bot:', error));
    } else {
        startBtn.disabled = true;
    }
});

// Check for stored private key on page load
function checkStoredWallet() {
    const storedKey = sessionStorage.getItem('dice_bot_pk');
    if (storedKey) {
        // Auto-reconnect with stored key
        privateKeyInput.value = storedKey;
        connectWalletBtn.click();
    } else {
        // No stored key, disable start button
        startBtn.disabled = true;
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Initial fetch of stats and settings
    updateStats();
    fetchSettings();
    
    // Check for stored wallet
    checkStoredWallet();
    
    // Set up polling for updates
    setInterval(updateStats, 1000);
});
