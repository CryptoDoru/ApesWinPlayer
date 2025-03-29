// DOM Elements
const startBtn = document.getElementById('startBtn');
const stopBtn = document.getElementById('stopBtn');
const resetStatsBtn = document.getElementById('resetStatsBtn');
const clearLogsBtn = document.getElementById('clearLogsBtn');
const autoScrollBtn = document.getElementById('autoScrollBtn');
const logMessages = document.getElementById('logMessages');
const recentGames = document.getElementById('recentGames');

// Game status elements
const botStatus = document.getElementById('bot-status');
const currentBetContainer = document.getElementById('current-bet-container');
const betStatus = document.getElementById('bet-status');
const currentBetAmount = document.getElementById('current-bet-amount');
const lastBetResult = document.getElementById('last-bet-result');

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

// Settings elements - View mode
const minBet = document.getElementById('minBet');
const maxBet = document.getElementById('maxBet');
const winStreakRate = document.getElementById('winStreakRate');
const lossRecovery = document.getElementById('lossRecovery');
const chaseThreshold = document.getElementById('chaseThreshold');
const chaseMultiplier = document.getElementById('chaseMultiplier');

// Settings elements - Edit mode
let editSettingsBtn; 
let settingsViewMode;
let settingsEditMode;
let settingsForm;
let saveSettingsBtn;
let cancelSettingsBtn;
let resetDefaultsBtn;

// Initialize settings elements after DOM is fully loaded
function initSettingsElements() {
    console.log('Initializing settings elements');
    
    // Get references to all settings-related elements
    editSettingsBtn = document.getElementById('editSettingsBtn');
    settingsViewMode = document.getElementById('settings-view-mode');
    settingsEditMode = document.getElementById('settings-edit-mode');
    settingsForm = document.getElementById('settingsForm');
    saveSettingsBtn = document.getElementById('saveSettingsBtn');
    cancelSettingsBtn = document.getElementById('cancelSettingsBtn');
    resetDefaultsBtn = document.getElementById('resetDefaultsBtn');
    
    console.log('Edit Button Element:', editSettingsBtn);
    console.log('Settings View Mode Element:', settingsViewMode);
    console.log('Settings Edit Mode Element:', settingsEditMode);
    
    // Set up event listeners for settings buttons
    setupSettingsButtons();
}

// Settings inputs
const minBetInput = document.getElementById('minBetInput');
const maxBetInput = document.getElementById('maxBetInput');
const winStreakRateInput = document.getElementById('winStreakRateInput');
const lossRecoveryInput = document.getElementById('lossRecoveryInput');
const chaseThresholdInput = document.getElementById('chaseThresholdInput');
const chaseMultiplierInput = document.getElementById('chaseMultiplierInput');

// State
let autoScroll = true;
let botRunning = false;
let currentlyBetting = false;

// Stats state to prevent flashing/glitching
let currentStats = {
    current_balance: '0.00',
    s_token_balance: '0.00',
    win_streak: 0,
    loss_streak: 0,
    games_since_69: 0,
    total_games: 0,
    total_wins: 0,
    total_losses: 0,
    session_profit: 0,
    last_update: '',
    all_time_high: '0.00',
    log_messages: [],
    recent_games: [],
    current_bet: '0.00',
    last_result: '--'
};

// Functions
function updateStats() {
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            // Only update UI if we have valid data
            if (!data.current_balance) return;
            
            // Cache stats to prevent UI glitches
            currentStats = {...currentStats, ...data};
            
            // Update balances with icons (ensuring we have consistent decimal places)
            currentBalance.textContent = `${currentStats.current_balance} 🍌`;
            sTokenBalance.textContent = `${currentStats.s_token_balance} S`;
            
            // Update streak stats
            winStreak.textContent = currentStats.win_streak;
            lossStreak.textContent = currentStats.loss_streak;
            gamesSince69.textContent = currentStats.games_since_69;
            
            // Ensure performance metrics update properly
            totalGames.textContent = currentStats.total_games;
            totalWins.textContent = currentStats.total_wins;
            totalLosses.textContent = currentStats.total_losses;
            
            // Display session profit with color coding
            const profit = currentStats.session_profit;
            sessionProfit.textContent = profit > 0 ? `+${profit}` : profit;
            sessionProfit.style.color = profit > 0 ? 'green' : profit < 0 ? 'red' : 'inherit';
            
            // Calculate win rate
            const calculatedWinRate = currentStats.total_games > 0 
                ? ((currentStats.total_wins / currentStats.total_games) * 100).toFixed(1)
                : 0;
            winRate.textContent = `${calculatedWinRate}%`;
            
            lastUpdate.textContent = currentStats.last_update || 'Never';
            allTimeHigh.textContent = currentStats.all_time_high;
            
            // Update betting information if available
            if (data.current_bet && botRunning) {
                currentBetAmount.textContent = `${data.current_bet} 🍌`;
                currentStats.current_bet = data.current_bet;
                
                // Make sure the bet container is visible when bot is running
                currentBetContainer.style.display = 'flex';
            }
            
            // Update game status indicator
            updateGameStatus();
            
            // Extract last bet result from recent games if available
            if (data.recent_games && data.recent_games.length > 0) {
                const lastGame = data.recent_games[0];
                const result = lastGame.won ? 'WIN' : 'LOSS';
                lastBetResult.textContent = result;
                lastBetResult.className = 'bet-value ' + (lastGame.won ? 'win-result' : 'loss-result');
                currentStats.last_result = result;
            }
            
            // Update log messages
            updateLogs(currentStats.log_messages);
            
            // Update recent games
            updateRecentGames(currentStats.recent_games);
            
            // Check for wallet status
            if (data.wallet_connected) {
                updateWalletUI(true, data.wallet_address);
            }
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

// Function to update game status indicator and betting animation
function updateGameStatus() {
    // If bot is not running, status is already set by start/stop functions
    if (!botRunning) return;
    
    // Check logs for betting activity - get the most recent logs
    const recentLogs = (currentStats.log_messages || []).slice(-15);
    
    // Direct extraction of current bet amount from logs
    const betDetailsLog = recentLogs.find(log => {
        const text = log.message || '';
        return text.includes('Final Amount:');
    });
    
    if (betDetailsLog) {
        const text = betDetailsLog.message || '';
        const matches = text.match(/Final Amount:\s+([\d\.]+)\s+🍌/);
        if (matches && matches[1]) {
            // Extract the bet amount and update UI immediately
            const betAmount = matches[1];
            currentBetAmount.textContent = `${betAmount} 🍌`;
            currentStats.current_bet = betAmount;
            currentBetContainer.style.display = 'flex';
            console.log('Extracted bet amount from logs:', betAmount);
        }
    }
    
    // Variables to track game state
    let isPlacingBet = false;
    let isWaitingForResult = false;
    let hasResult = false;
    let isCalculatingNextBet = false;
    let resultWin = false;
    
    // Scan for specific game state indicators
    for (const log of recentLogs) {
        const text = log.message || '';
        
        // Check for bet placement indicators
        if (text.includes('🎲 PLACING BET 🎲') || 
            text.includes('BET DETAILS') || 
            text.includes('Base Amount:') || 
            text.includes('Final Amount:')) {
            isPlacingBet = true;
        }
        
        // Check for waiting indicators
        if (text.includes('Transaction Success') || 
            text.includes('Waiting for game result') || 
            text.includes('Gas Info') || 
            text.includes('Game in progress')) {
            isWaitingForResult = true;
        }
        
        // Check for result indicators
        if (text.includes('RESULT:')) {
            hasResult = true;
            resultWin = text.includes('WON');
        }
        
        // More specific win/loss detection
        // Check exact patterns from bot.py logs
        if (text.includes('✨ WIN:') || text.includes('WIN STREAK:')) {
            hasResult = true;
            resultWin = true;
            console.log('Win detected from log: ' + text);
        }
        
        if (text.includes('📉 LOSS:') || text.includes('LOSS STREAK:')) {
            hasResult = true;
            resultWin = false;
            console.log('Loss detected from log: ' + text);
        }
        
        // Check for next bet calculation
        if (text.includes('NEXT BET:')) {
            isCalculatingNextBet = true;
        }
    }
    
    // Always show the bet container when bot is running
    if (botRunning) {
        currentBetContainer.style.display = 'flex';
    }
    
    // Update UI based on current game state - prioritized by sequence
    if (isPlacingBet && !hasResult) {
        console.log('Status: PLACING BET');
        botStatus.textContent = 'BETTING';
        botStatus.className = 'status-indicator betting';
        betStatus.textContent = 'Placing bet...';
        currentlyBetting = true;
        
        // Force a refresh of current bet
        fetchCurrentBet();
    } 
    else if (isWaitingForResult && !hasResult) {
        console.log('Status: WAITING FOR RESULT');
        botStatus.textContent = 'WAITING';
        botStatus.className = 'status-indicator betting';
        betStatus.textContent = 'Waiting for game result...';
        currentlyBetting = true;
    } 
    else if (hasResult) {
        console.log('Status: GAME RESULT - ' + (resultWin ? 'WIN' : 'LOSS'));
        botStatus.textContent = resultWin ? 'WIN' : 'LOSS';
        botStatus.className = `status-indicator ${resultWin ? 'win' : 'loss'}`;
        betStatus.textContent = `Game complete - ${resultWin ? 'Won!' : 'Lost'}`;
        
        // Update last result display
        lastBetResult.textContent = resultWin ? 'WIN' : 'LOSS';
        lastBetResult.className = resultWin ? 'win-result' : 'loss-result';
    } 
    else if (isCalculatingNextBet) {
        console.log('Status: CALCULATING NEXT BET');
        botStatus.textContent = 'PLANNING';
        botStatus.className = 'status-indicator online';
        betStatus.textContent = 'Calculating next bet...';
    } 
    else if (botRunning) {
        console.log('Status: WAITING FOR NEXT BET');
        botStatus.textContent = 'ONLINE';
        botStatus.className = 'status-indicator online';
        betStatus.textContent = 'Waiting for next bet...';
        currentlyBetting = false;
    }
}

// Function to specifically fetch current bet information in real-time
function fetchCurrentBet() {
    if (!botRunning) return;
    
    console.log('Fetching current bet amount...');
    
    fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            console.log('Received stats data:', data);
            
            if (data && data.current_bet) {
                console.log('Current bet found:', data.current_bet);
                
                // Update only the bet amount in the UI
                currentBetAmount.textContent = `${data.current_bet} 🍌`;
                currentStats.current_bet = data.current_bet;
                
                // Make sure bet container is visible
                currentBetContainer.style.display = 'flex';
            } else {
                console.log('No current bet found in data');
                
                // Try to extract from logs as fallback
                if (data && data.log_messages && data.log_messages.length > 0) {
                    const logs = data.log_messages;
                    
                    // Look for "Final Amount:" log entry
                    const betLog = logs.find(log => {
                        return (log.message || '').includes('Final Amount:');
                    });
                    
                    if (betLog) {
                        const text = betLog.message || '';
                        const matches = text.match(/Final Amount:\s+([\d\.]+)\s+🍌/);
                        if (matches && matches[1]) {
                            console.log('Extracted bet from logs:', matches[1]);
                            currentBetAmount.textContent = `${matches[1]} 🍌`;
                            currentStats.current_bet = matches[1];
                            currentBetContainer.style.display = 'flex';
                        }
                    }
                }
            }
        })
        .catch(error => {
            console.error('Error fetching current bet:', error);
        });
}

function updateRecentGames(games) {
    if (!games || games.length === 0) {
        recentGames.innerHTML = '<div class="loading-message">No games played yet</div>';
        return;
    }
    
    // Update the last bet result if we have games
    if (games.length > 0) {
        const lastGame = games[0];
        
        // Format the outcome for display
        let resultDisplay = lastGame.win ? '<span class="win-result">WIN</span>' : '<span class="loss-result">LOSS</span>';
        
        // Special styling for 69 pattern
        if (lastGame.has_pattern) {
            resultDisplay = '<span class="pattern-result">69 WIN</span>';
        }
        
        // Update the last bet result display
        lastBetResult.innerHTML = resultDisplay;
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

// Set up event listeners for sliders to update display values in real-time
function setupSliderEventListeners() {
    // Main strategy sliders
    minBetInput.addEventListener('input', function() {
        document.getElementById('minBetDisplay').textContent = `${this.value}%`;
    });
    
    maxBetInput.addEventListener('input', function() {
        document.getElementById('maxBetDisplay').textContent = `${this.value}%`;
    });
    
    winStreakRateInput.addEventListener('input', function() {
        document.getElementById('winStreakRateDisplay').textContent = `${this.value}%`;
    });
    
    lossRecoveryInput.addEventListener('input', function() {
        document.getElementById('lossRecoveryDisplay').textContent = `${this.value}%`;
    });
    
    chaseThresholdInput.addEventListener('input', function() {
        document.getElementById('chaseThresholdDisplay').textContent = this.value;
    });
    
    chaseMultiplierInput.addEventListener('input', function() {
        document.getElementById('chaseMultiplierDisplay').textContent = `${parseFloat(this.value).toFixed(2)}x`;
    });
    
    // Advanced strategy sliders
    if (document.getElementById('winSensitivityInput')) {
        document.getElementById('winSensitivityInput').addEventListener('input', function() {
            document.getElementById('winSensitivityDisplay').textContent = `${this.value}%`;
        });
    }
    
    if (document.getElementById('lossSensitivityInput')) {
        document.getElementById('lossSensitivityInput').addEventListener('input', function() {
            document.getElementById('lossSensitivityDisplay').textContent = `${this.value}%`;
        });
    }
    
    if (document.getElementById('maxTrackGamesInput')) {
        document.getElementById('maxTrackGamesInput').addEventListener('input', function() {
            document.getElementById('maxTrackGamesDisplay').textContent = this.value;
        });
    }
}

function fetchSettings() {
    fetch('/api/current_settings')
        .then(response => response.json())
        .then(data => {
            // Update display values
            minBet.textContent = `${(data.min_bet_percentage * 100).toFixed(0)}%`;
            maxBet.textContent = `${(data.max_bet_percentage * 100).toFixed(0)}%`;
            winStreakRate.textContent = `${(data.win_streak_rate * 100).toFixed(0)}%`;
            lossRecovery.textContent = `${(data.loss_recovery_rate * 100).toFixed(0)}%`;
            chaseThreshold.textContent = data.chase_69_threshold;
            chaseMultiplier.textContent = `${data.chase_69_multiplier}x`;
            
            // Update advanced strategy parameters in view mode
            if (data.win_sensitivity !== undefined) {
                document.getElementById('winSensitivity').textContent = `${(data.win_sensitivity * 100).toFixed(0)}%`;
            }
            if (data.loss_sensitivity !== undefined) {
                document.getElementById('lossSensitivity').textContent = `${(data.loss_sensitivity * 100).toFixed(0)}%`;
            }
            if (data.max_track_games !== undefined) {
                document.getElementById('maxTrackGames').textContent = data.max_track_games;
            }
            
            // Also update form input values and displays
            minBetInput.value = (data.min_bet_percentage * 100).toFixed(0);
            document.getElementById('minBetDisplay').textContent = `${(data.min_bet_percentage * 100).toFixed(0)}%`;
            
            maxBetInput.value = (data.max_bet_percentage * 100).toFixed(0);
            document.getElementById('maxBetDisplay').textContent = `${(data.max_bet_percentage * 100).toFixed(0)}%`;
            
            winStreakRateInput.value = (data.win_streak_rate * 100).toFixed(0);
            document.getElementById('winStreakRateDisplay').textContent = `${(data.win_streak_rate * 100).toFixed(0)}%`;
            
            lossRecoveryInput.value = (data.loss_recovery_rate * 100).toFixed(0);
            document.getElementById('lossRecoveryDisplay').textContent = `${(data.loss_recovery_rate * 100).toFixed(0)}%`;
            
            chaseThresholdInput.value = data.chase_69_threshold;
            document.getElementById('chaseThresholdDisplay').textContent = data.chase_69_threshold;
            
            chaseMultiplierInput.value = data.chase_69_multiplier.toFixed(2);
            document.getElementById('chaseMultiplierDisplay').textContent = `${data.chase_69_multiplier.toFixed(2)}x`;
            
            // Update advanced strategy parameters if they exist
            if (data.win_sensitivity !== undefined) {
                document.getElementById('winSensitivityInput').value = (data.win_sensitivity * 100).toFixed(0);
                document.getElementById('winSensitivityDisplay').textContent = `${(data.win_sensitivity * 100).toFixed(0)}%`;
            }
            if (data.loss_sensitivity !== undefined) {
                document.getElementById('lossSensitivityInput').value = (data.loss_sensitivity * 100).toFixed(0);
                document.getElementById('lossSensitivityDisplay').textContent = `${(data.loss_sensitivity * 100).toFixed(0)}%`;
            }
            if (data.max_track_games !== undefined) {
                document.getElementById('maxTrackGamesInput').value = data.max_track_games;
                document.getElementById('maxTrackGamesDisplay').textContent = data.max_track_games;
            }
            
            // Set up slider event listeners after values are populated
            setupSliderEventListeners();
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
                
                // Update the bot status to online
                botStatus.textContent = 'ONLINE';
                botStatus.className = 'status-indicator online';
                
                // Show the betting container
                currentBetContainer.style.display = 'flex';
                
                // Immediately fetch fresh stats to get current bet amount
                setTimeout(() => {
                    fetch('/api/stats')
                        .then(response => response.json())
                        .then(statsData => {
                            if (statsData.current_bet) {
                                currentBetAmount.textContent = `${statsData.current_bet} 🍌`;
                                currentStats.current_bet = statsData.current_bet;
                            }
                        })
                        .catch(err => console.error('Error fetching initial bet data:', err));
                }, 500); // Small delay to allow server to update
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
                
                // Update the bot status to offline
                botStatus.textContent = 'OFFLINE';
                botStatus.className = 'status-indicator offline';
                
                // Hide the betting container
                currentBetContainer.style.display = 'none';
                currentlyBetting = false;
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

// Function to set up event listeners for settings buttons
function setupSettingsButtons() {
    console.log('Setting up settings buttons');
    
    // Edit button - Switch to edit mode
    if (editSettingsBtn) {
        editSettingsBtn.onclick = function() {
            console.log('Edit Settings button clicked');
            settingsViewMode.style.display = 'none';
            settingsEditMode.style.display = 'block';
        };
        console.log('Edit button handler attached');
    } else {
        console.error('Edit Settings button not found');
    }
    
    // Cancel button - Return to view mode without saving
    if (cancelSettingsBtn) {
        cancelSettingsBtn.onclick = function() {
            console.log('Cancel Settings button clicked');
            settingsEditMode.style.display = 'none';
            settingsViewMode.style.display = 'block';
            fetchSettings(); // Reset form to current settings
        };
    }
    
    // Reset to defaults button
    if (resetDefaultsBtn) {
        resetDefaultsBtn.onclick = function() {
            console.log('Reset Defaults button clicked');
            // Set default values for all settings
            minBetInput.value = '10';
            maxBetInput.value = '25';
            winStreakRateInput.value = '20';
            lossRecoveryInput.value = '15';
            chaseThresholdInput.value = '15';
            chaseMultiplierInput.value = '1.10';
            
            // Advanced settings defaults
            winSensitivityInput.value = '50';
            lossSensitivityInput.value = '50';
            maxTrackGamesInput.value = '20';
            
            // Update all display values
            document.getElementById('minBetDisplay').textContent = '10%';
            document.getElementById('maxBetDisplay').textContent = '25%';
            document.getElementById('winStreakRateDisplay').textContent = '20%';
            document.getElementById('lossRecoveryDisplay').textContent = '15%';
            document.getElementById('chaseThresholdDisplay').textContent = '15';
            document.getElementById('chaseMultiplierDisplay').textContent = '1.10x';
            document.getElementById('winSensitivityDisplay').textContent = '50%';
            document.getElementById('lossSensitivityDisplay').textContent = '50%';
            document.getElementById('maxTrackGamesDisplay').textContent = '20';
        };
    }
    
    // Set up slider event listeners
    setupSliderEventListeners();
    
    // Save settings button
    if (saveSettingsBtn) {
        saveSettingsBtn.onclick = function() {
            console.log('Save Settings button clicked');
            
            // Validate inputs
            if (parseInt(minBetInput.value) >= parseInt(maxBetInput.value)) {
                alert('Min bet percentage must be less than max bet percentage');
                return;
            }
            
            // Prepare settings data
            const settings = {
                min_bet_percentage: parseInt(minBetInput.value) / 100,
                max_bet_percentage: parseInt(maxBetInput.value) / 100,
                win_streak_rate: parseInt(winStreakRateInput.value) / 100,
                loss_recovery_rate: parseInt(lossRecoveryInput.value) / 100,
                chase_69_threshold: parseInt(chaseThresholdInput.value),
                chase_69_multiplier: parseFloat(chaseMultiplierInput.value),
                win_sensitivity: parseInt(document.getElementById('winSensitivityInput').value) / 100,
                loss_sensitivity: parseInt(document.getElementById('lossSensitivityInput').value) / 100,
                max_track_games: parseInt(document.getElementById('maxTrackGamesInput').value)
            };
            
            // Save settings to the server
            fetch('/api/save_settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    // Update displayed settings
                    fetchSettings();
                    
                    // Switch back to view mode
                    settingsEditMode.style.display = 'none';
                    settingsViewMode.style.display = 'block';
                    
                    // Add success message
                    addLogMessage('INFO', 'Bot settings updated successfully');
                } else {
                    alert('Failed to save settings: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Error saving settings:', error);
                alert('An error occurred while saving settings');
            });
        };
    }
}

// Apply same fix to other settings buttons
if (resetDefaultsBtn) {
    resetDefaultsBtn.addEventListener('click', function() {
        console.log('Reset Defaults button clicked');
        // Reset form values to defaults
        minBetInput.value = '10';
        maxBetInput.value = '25';
        winStreakRateInput.value = '20';
        lossRecoveryInput.value = '15';
        chaseThresholdInput.value = '15';
        chaseMultiplierInput.value = '1.10';
    });
}

if (saveSettingsBtn) {
    saveSettingsBtn.addEventListener('click', function() {
        console.log('Save Settings button clicked');
        // Validate form inputs
        if (parseInt(minBetInput.value) >= parseInt(maxBetInput.value)) {
            alert('Min bet percentage must be less than max bet percentage');
            return;
        }
    
    // Prepare settings data
    const settings = {
        min_bet_percentage: parseInt(minBetInput.value) / 100,
        max_bet_percentage: parseInt(maxBetInput.value) / 100,
        win_streak_rate: parseInt(winStreakRateInput.value) / 100,
        loss_recovery_rate: parseInt(lossRecoveryInput.value) / 100,
        chase_69_threshold: parseInt(chaseThresholdInput.value),
        chase_69_multiplier: parseFloat(chaseMultiplierInput.value),
        // New advanced strategy parameters
        win_sensitivity: parseInt(document.getElementById('winSensitivityInput').value) / 100,
        loss_sensitivity: parseInt(document.getElementById('lossSensitivityInput').value) / 100,
        max_track_games: parseInt(document.getElementById('maxTrackGamesInput').value)
    };
    
    // Save settings to the server
    fetch('/api/save_settings', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(settings)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Update displayed settings
            fetchSettings();
            
            // Switch back to view mode
            settingsEditMode.style.display = 'none';
            settingsViewMode.style.display = 'block';
            
            // Add success message to logs
            addLogMessage('INFO', 'Bot settings updated successfully');
        } else {
            alert('Failed to save settings: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error saving settings:', error);
        alert('An error occurred while saving settings');
    });
    });
}

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
            // Update the UI with the new wallet info
            updateWalletUI(true, data.wallet_address);
            
            // Update cached stats to prevent glitching
            currentStats.current_balance = data.current_balance || '0.00';
            currentStats.s_token_balance = data.s_token_balance || '0.00';
            
            // Update the balance displays
            currentBalance.textContent = `${currentStats.current_balance} 🍌`;
            sTokenBalance.textContent = `${currentStats.s_token_balance} S`;
            
            // Store the private key in session storage (not local storage for security)
            // This allows reconnection if page is refreshed
            sessionStorage.setItem('dice_bot_pk', privateKey);
            
            // Clear the input for security
            privateKeyInput.value = '';
            
            // Force an immediate stats update
            setTimeout(updateStats, 100);
        } else {
            // Show error
            alert('Error connecting wallet: ' + (data.message || 'Unknown error'));
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

// Update wallet UI based on connection status
function updateWalletUI(connected, address = null) {
    if (connected) {
        walletConnected = true;
        walletDisconnectedView.style.display = 'none';
        walletConnectedView.style.display = 'block';
        
        if (address) {
            // Display wallet address with truncation
            const truncatedAddress = `${address.substring(0, 6)}...${address.substring(address.length - 4)}`;
            connectedAddress.textContent = truncatedAddress;
            connectedAddress.title = address; // Full address on hover
        }
        
        // Enable start button
        startBtn.disabled = false;
    } else {
        walletConnected = false;
        walletConnectedView.style.display = 'none';
        walletDisconnectedView.style.display = 'block';
        
        // Clear address
        connectedAddress.textContent = '';
        connectedAddress.title = '';
        
        // Disable start button
        startBtn.disabled = true;
    }
}

// Check for stored private key on page load
function checkStoredWallet() {
    const storedKey = sessionStorage.getItem('dice_bot_pk');
    if (storedKey) {
        // Auto-reconnect with stored key
        reconnectWallet(storedKey);
    } else {
        // No stored key, disable start button
        startBtn.disabled = true;
    }
}

// Helper function to reconnect wallet from session storage
function reconnectWallet(privateKey) {
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
            updateWalletUI(true, data.wallet_address);
            
            // Update balances
            if (data.current_balance) {
                currentStats.current_balance = data.current_balance;
                currentStats.s_token_balance = data.s_token_balance;
                
                currentBalance.textContent = `${data.current_balance} 🍌`;
                sTokenBalance.textContent = `${data.s_token_balance} S`;
            }
        } else {
            // Failed to reconnect with stored key
            sessionStorage.removeItem('dice_bot_pk');
            console.error("Failed to reconnect with stored key");
        }
    })
    .catch(error => {
        console.error('Error reconnecting wallet:', error);
        sessionStorage.removeItem('dice_bot_pk');
    });
}

// Theme toggle functionality
const toggleSwitch = document.getElementById('checkbox');

// Function to switch theme
function switchTheme(e) {
    if (e.target.checked) {
        document.documentElement.setAttribute('data-theme', 'dark');
        localStorage.setItem('theme', 'dark');
        console.log('Dark mode enabled');
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
        console.log('Light mode enabled');
    }
}

// Function to initialize theme based on user preference
function initTheme() {
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    if (currentTheme === 'dark') {
        document.documentElement.setAttribute('data-theme', 'dark');
        toggleSwitch.checked = true;
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        toggleSwitch.checked = false;
    }
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM Content Loaded - initializing dashboard');
    
    // Initialize theme toggle
    initTheme();
    toggleSwitch.addEventListener('change', switchTheme, false);
    
    // Initialize settings elements and listeners first
    initSettingsElements();
    
    // Initial fetch of stats and settings
    updateStats();
    fetchSettings();
    
    // Check for stored wallet
    checkStoredWallet();
    
    // Initialize game status indicators
    botStatus.textContent = 'OFFLINE';
    botStatus.className = 'status-indicator offline';
    currentBetContainer.style.display = 'none';
    
    // Set up polling for updates
    setInterval(() => {
        updateStats();
        
        // If bot is actively betting, fetch current bet info more frequently
        if (botRunning && currentlyBetting) {
            fetchCurrentBet();
        }
    }, 1000);
    
    // Very frequent update for game status to catch bet placement immediately
    setInterval(() => {
        if (botRunning) {
            fetchLogs();
            updateGameStatus();
        }
    }, 500);
    
    // Debug help - log status every few seconds when running
    setInterval(() => {
        if (botRunning && currentBetContainer.style.display === 'flex') {
            console.log('Current bet display active, showing: ' + currentBetAmount.textContent);
        }
    }, 5000);
});

// No duplicate declaration needed as it's already defined at line 52
