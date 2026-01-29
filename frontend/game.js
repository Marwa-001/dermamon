let gameState = {
    score: 0,
    timeLeft: 60,
    highScore: 0,
    combo: 0,
    isPlaying: false,
    isPaused: false,
    gameInterval: null,
    spawnInterval: null,
    speedIncreaseInterval: null,
    dermamons: [],
    balloons: [],
    particles: [],
    canvas: null,
    ctx: null,
    baseSpeed: 2,
    currentSpeed: 2,
    speedMultiplier: 1
};

// Game Toggle
function toggleGame() {
    const gamePopup = document.getElementById('gamePopup');
    const gameCorner = document.getElementById('gameCorner');
    
    gamePopup.classList.toggle('active');
    
    if (gamePopup.classList.contains('active')) {
        gameCorner.style.display = 'none';
        if (!gameState.canvas) {
            setTimeout(initGame, 100);
        }
    } else {
        gameCorner.style.display = 'block';
        if (gameState.isPlaying) {
            pauseGame();
        }
    }
}

// Game Toggle
function toggleGame() {
    const gamePopup = document.getElementById('gamePopup');
    const gameWidget = document.getElementById('gameWidget');
    
    gamePopup.classList.toggle('active');
    
    if (gamePopup.classList.contains('active')) {
        gameWidget.style.display = 'none';
        if (!gameState.canvas) {
            setTimeout(initGame, 100);
        }
    } else {
        gameWidget.style.display = 'block';
        if (gameState.isPlaying) {
            pauseGame();
        }
    }
}

// Initialize Game
function initGame() {
    gameState.canvas = document.getElementById('gameCanvas');
    if (!gameState.canvas) return;
    
    gameState.ctx = gameState.canvas.getContext('2d');
    
    // Load high score
    const savedHighScore = localStorage.getItem('dermamonHighScore');
    if (savedHighScore) {
        gameState.highScore = parseInt(savedHighScore);
        document.getElementById('highScore').textContent = gameState.highScore;
    }
    
    // Add click listener
    gameState.canvas.addEventListener('click', handleCanvasClick);
    
    // Load leaderboard
    loadLeaderboard();
}

// Game Entities
class Dermamon {
    constructor(speedMultiplier = 1) {
        this.x = Math.random() * (gameState.canvas.width - 80) + 40;
        this.y = Math.random() * (gameState.canvas.height - 80) + 40;
        this.size = 60;
        this.speedX = (Math.random() - 0.5) * gameState.baseSpeed * speedMultiplier;
        this.speedY = (Math.random() - 0.5) * gameState.baseSpeed * speedMultiplier;
        this.emoji = '🧴';
        this.hit = false;
    }
    
    update() {
        this.x += this.speedX;
        this.y += this.speedY;
        
        // Bounce off walls
        if (this.x < this.size/2 || this.x > gameState.canvas.width - this.size/2) {
            this.speedX *= -1;
        }
        if (this.y < this.size/2 || this.y > gameState.canvas.height - this.size/2) {
            this.speedY *= -1;
        }
        
        // Keep in bounds
        this.x = Math.max(this.size/2, Math.min(gameState.canvas.width - this.size/2, this.x));
        this.y = Math.max(this.size/2, Math.min(gameState.canvas.height - this.size/2, this.y));
    }
    
    draw(ctx) {
        ctx.font = `${this.size}px Arial`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(this.emoji, this.x, this.y);
        
        // Draw glow effect
        if (!this.hit) {
            ctx.shadowColor = '#6366f1';
            ctx.shadowBlur = 15;
            ctx.fillText(this.emoji, this.x, this.y);
            ctx.shadowBlur = 0;
        }
    }
    
    isClicked(mx, my) {
        const distance = Math.sqrt((mx - this.x) ** 2 + (my - this.y) ** 2);
        return distance < this.size / 2;
    }
}

class Balloon {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.size = 0;
        this.maxSize = 50;
        this.growing = true;
        this.opacity = 1;
    }
    
    update() {
        if (this.growing) {
            this.size += 5;
            if (this.size >= this.maxSize) {
                this.growing = false;
            }
        } else {
            this.opacity -= 0.05;
        }
        return this.opacity > 0;
    }
    
    draw(ctx) {
        ctx.save();
        ctx.globalAlpha = this.opacity;
        ctx.fillStyle = '#4FC3F7';
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
        
        // Water droplets
        ctx.fillStyle = 'rgba(255, 255, 255, 0.5)';
        for (let i = 0; i < 5; i++) {
            const angle = (Math.PI * 2 / 5) * i;
            const dx = Math.cos(angle) * this.size * 0.6;
            const dy = Math.sin(angle) * this.size * 0.6;
            ctx.beginPath();
            ctx.arc(this.x + dx, this.y + dy, 5, 0, Math.PI * 2);
            ctx.fill();
        }
        ctx.restore();
    }
}

class Particle {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.speedX = (Math.random() - 0.5) * 8;
        this.speedY = (Math.random() - 0.5) * 8;
        this.size = Math.random() * 10 + 5;
        this.life = 1;
        this.color = ['💧', '💦', '✨'][Math.floor(Math.random() * 3)];
    }
    
    update() {
        this.x += this.speedX;
        this.y += this.speedY;
        this.speedY += 0.2;
        this.life -= 0.02;
        return this.life > 0;
    }
    
    draw(ctx) {
        ctx.save();
        ctx.globalAlpha = this.life;
        ctx.font = `${this.size}px Arial`;
        ctx.textAlign = 'center';
        ctx.fillText(this.color, this.x, this.y);
        ctx.restore();
    }
}

// Game Logic
function startGame() {
    if (gameState.isPlaying) return;
    
    gameState.isPlaying = true;
    gameState.isPaused = false;
    gameState.score = 0;
    gameState.timeLeft = 60;
    gameState.combo = 0;
    gameState.dermamons = [];
    gameState.balloons = [];
    gameState.particles = [];
    gameState.currentSpeed = gameState.baseSpeed;
    gameState.speedMultiplier = 1;
    
    updateScore();
    
    document.getElementById('startBtn').style.display = 'none';
    document.getElementById('pauseBtn').style.display = 'inline-block';
    
    // Spawn initial Dermamons (slow)
    for (let i = 0; i < 2; i++) {
        gameState.dermamons.push(new Dermamon(gameState.speedMultiplier));
    }
    
    // Game timer
    gameState.gameInterval = setInterval(() => {
        if (!gameState.isPaused) {
            gameState.timeLeft--;
            document.getElementById('gameTime').textContent = gameState.timeLeft;
            
            if (gameState.timeLeft <= 0) {
                endGame();
            }
        }
    }, 1000);
    
    // Spawn new Dermamons
    gameState.spawnInterval = setInterval(() => {
        if (!gameState.isPaused && gameState.dermamons.length < 5) {
            gameState.dermamons.push(new Dermamon(gameState.speedMultiplier));
        }
    }, 3000);
    
    // Speed increase every 10 seconds
    gameState.speedIncreaseInterval = setInterval(() => {
        if (!gameState.isPaused) {
            gameState.speedMultiplier += 0.3;
            // Update existing Dermamons speed
            gameState.dermamons.forEach(d => {
                d.speedX *= 1.15;
                d.speedY *= 1.15;
            });
            
            // Visual feedback
            const ctx = gameState.ctx;
            ctx.save();
            ctx.fillStyle = 'rgba(255, 107, 107, 0.3)';
            ctx.fillRect(0, 0, gameState.canvas.width, gameState.canvas.height);
            ctx.fillStyle = 'white';
            ctx.font = 'bold 32px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('SPEED UP! 🚀', gameState.canvas.width / 2, gameState.canvas.height / 2);
            ctx.restore();
        }
    }, 10000);
    
    // Start game loop
    gameLoop();
}

function pauseGame() {
    gameState.isPaused = !gameState.isPaused;
    document.getElementById('pauseBtn').textContent = gameState.isPaused ? 'Resume' : 'Pause';
}

function resetGame() {
    endGame();
    gameState.score = 0;
    gameState.timeLeft = 60;
    gameState.combo = 0;
    gameState.speedMultiplier = 1;
    updateScore();
    clearCanvas();
}

function endGame() {
    gameState.isPlaying = false;
    clearInterval(gameState.gameInterval);
    clearInterval(gameState.spawnInterval);
    clearInterval(gameState.speedIncreaseInterval);
    
    document.getElementById('startBtn').style.display = 'inline-block';
    document.getElementById('pauseBtn').style.display = 'none';
    
    // Save high score
    if (gameState.score > gameState.highScore) {
        gameState.highScore = gameState.score;
        localStorage.setItem('dermamonHighScore', gameState.highScore);
        document.getElementById('highScore').textContent = gameState.highScore;
        showSuccess(`🎉 New High Score: ${gameState.highScore}!`);
    }
    
    // Save to leaderboard
    saveScore(gameState.score);
    
    // Show game over
    const ctx = gameState.ctx;
    ctx.fillStyle = 'rgba(0, 0, 0, 0.7)';
    ctx.fillRect(0, 0, gameState.canvas.width, gameState.canvas.height);
    
    ctx.fillStyle = 'white';
    ctx.font = 'bold 48px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('Game Over!', gameState.canvas.width / 2, gameState.canvas.height / 2 - 50);
    
    ctx.font = '32px Arial';
    ctx.fillText(`Final Score: ${gameState.score}`, gameState.canvas.width / 2, gameState.canvas.height / 2 + 10);
    
    ctx.font = '24px Arial';
    ctx.fillText(`High Score: ${gameState.highScore}`, gameState.canvas.width / 2, gameState.canvas.height / 2 + 50);
}

function gameLoop() {
    if (!gameState.isPlaying) return;
    
    clearCanvas();
    
    if (!gameState.isPaused) {
        // Update and draw Dermamons
        gameState.dermamons.forEach(d => {
            d.update();
            d.draw(gameState.ctx);
        });
        
        // Update and draw balloons
        gameState.balloons = gameState.balloons.filter(b => {
            const alive = b.update();
            if (alive) b.draw(gameState.ctx);
            return alive;
        });
        
        // Update and draw particles
        gameState.particles = gameState.particles.filter(p => {
            const alive = p.update();
            if (alive) p.draw(gameState.ctx);
            return alive;
        });
    } else {
        // Draw paused state
        gameState.dermamons.forEach(d => d.draw(gameState.ctx));
        
        gameState.ctx.fillStyle = 'rgba(0, 0, 0, 0.5)';
        gameState.ctx.fillRect(0, 0, gameState.canvas.width, gameState.canvas.height);
        
        gameState.ctx.fillStyle = 'white';
        gameState.ctx.font = 'bold 48px Arial';
        gameState.ctx.textAlign = 'center';
        gameState.ctx.fillText('PAUSED', gameState.canvas.width / 2, gameState.canvas.height / 2);
    }
    
    requestAnimationFrame(gameLoop);
}

function clearCanvas() {
    const ctx = gameState.ctx;
    const gradient = ctx.createLinearGradient(0, 0, 0, gameState.canvas.height);
    gradient.addColorStop(0, '#87CEEB');
    gradient.addColorStop(1, '#E0F6FF');
    ctx.fillStyle = gradient;
    ctx.fillRect(0, 0, gameState.canvas.width, gameState.canvas.height);
}

function handleCanvasClick(e) {
    if (!gameState.isPlaying || gameState.isPaused) return;
    
    const rect = gameState.canvas.getBoundingClientRect();
    const scaleX = gameState.canvas.width / rect.width;
    const scaleY = gameState.canvas.height / rect.height;
    const x = (e.clientX - rect.left) * scaleX;
    const y = (e.clientY - rect.top) * scaleY;
    
    let hit = false;
    
    gameState.dermamons = gameState.dermamons.filter(d => {
        if (d.isClicked(x, y) && !d.hit) {
            d.hit = true;
            hit = true;
            
            // Create effects
            gameState.balloons.push(new Balloon(d.x, d.y));
            for (let i = 0; i < 15; i++) {
                gameState.particles.push(new Particle(d.x, d.y));
            }
            
            // Update score
            gameState.combo++;
            const points = 10 * gameState.combo;
            gameState.score += points;
            updateScore();
            
            showScorePopup(d.x, d.y, `+${points}`);
            
            return false;
        }
        return true;
    });
    
    if (!hit) {
        gameState.combo = 0;
        document.getElementById('gameCombo').textContent = gameState.combo;
    }
}

function updateScore() {
    document.getElementById('gameScore').textContent = gameState.score;
    document.getElementById('gameCombo').textContent = gameState.combo;
}

function showScorePopup(x, y, text) {
    const ctx = gameState.ctx;
    ctx.save();
    ctx.fillStyle = '#10b981';
    ctx.font = 'bold 32px Arial';
    ctx.textAlign = 'center';
    ctx.fillText(text, x, y - 40);
    ctx.restore();
}

// Leaderboard
async function saveScore(score) {
    try {
        const res = await fetch(`${API_URL}/game/score`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': userToken ? `Bearer ${userToken}` : ''
            },
            body: JSON.stringify({
                score: score,
                game_type: 'balloon_hit',
                user_id: currentUser || 'guest'
            })
        });
        
        if (res.ok) {
            loadLeaderboard();
        }
    } catch (err) {
        console.log('Failed to save score:', err);
    }
}

async function loadLeaderboard() {
    try {
        const res = await fetch(`${API_URL}/game/leaderboard`);
        const data = await res.json();
        
        if (data.success && data.leaderboard) {
            displayLeaderboard(data.leaderboard);
        }
    } catch (err) {
        console.log('Failed to load leaderboard');
    }
}

function displayLeaderboard(scores) {
    const list = document.getElementById('leaderboardList');
    if (!list) return;
    
    const medals = ['🥇', '🥈', '🥉'];
    
    list.innerHTML = scores.slice(0, 10).map((s, i) => `
        <div class="leaderboard-item">
            <span class="leaderboard-rank">
                ${i < 3 ? `<span class="medal">${medals[i]}</span>` : ''}${i + 1}
            </span>
            <span class="leaderboard-name">${s.user_id || 'Guest'}</span>
            <span class="leaderboard-score">${s.score} pts</span>
        </div>
    `).join('');
}

function toggleLeaderboard() {
    document.getElementById('gameLeaderboard').classList.toggle('hidden');
}