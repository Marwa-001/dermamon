const API_URL = 'http://localhost:5000/api';
let userToken = null;
let currentUser = null;

// Check API Health
async function checkAPIHealth() {
    try {
        const res = await fetch(`${API_URL}/health`);
        const data = await res.json();
        document.getElementById('statusDot').className = 'status-dot status-online';
        document.getElementById('statusText').textContent = 'API Online';
        return true;
    } catch {
        document.getElementById('statusDot').className = 'status-dot status-offline';
        document.getElementById('statusText').textContent = 'API Offline';
        return false;
    }
}

// Utility Functions
function showError(msg) {
    const div = document.createElement('div');
    div.className = 'error-message';
    div.textContent = msg;
    const container = document.querySelector('.main-content');
    if (container) {
        container.insertBefore(div, container.firstChild);
        setTimeout(() => div.remove(), 5000);
    }
}

function showSuccess(msg) {
    const div = document.createElement('div');
    div.className = 'success-message';
    div.textContent = msg;
    const container = document.querySelector('.main-content');
    if (container) {
        container.insertBefore(div, container.firstChild);
        setTimeout(() => div.remove(), 5000);
    }
}

// Auth UI Updates
function updateAuthUI(isLoggedIn, userName = '') {
    const authButtons = document.getElementById('authButtons');
    const userSection = document.getElementById('userSection');
    const sidebarAuth = document.getElementById('sidebarAuth');
    const sidebarLogout = document.getElementById('sidebarLogout');
    
    if (isLoggedIn) {
        authButtons.style.display = 'none';
        userSection.style.display = 'flex';
        document.getElementById('userName').textContent = `Hi, ${userName}!`;
        
        sidebarAuth.style.display = 'none';
        sidebarLogout.style.display = 'block';
    } else {
        authButtons.style.display = 'flex';
        userSection.style.display = 'none';
        
        sidebarAuth.style.display = 'block';
        sidebarLogout.style.display = 'none';
    }
}

// Navigation Functions
function showSection(section) {
    document.getElementById('homeSection').classList.add('hidden');
    document.querySelectorAll('.form-section').forEach(f => f.classList.remove('active'));
    document.getElementById('results').classList.remove('active');
    
    if (section === 'home') {
        document.getElementById('homeSection').classList.remove('hidden');
    } else if (section === 'reviews') {
        closeAllForms();
        document.getElementById('reviewsSection').classList.add('active');
        document.getElementById('reviewsSection').scrollIntoView({behavior: 'smooth'});
    }
}

function closeAllForms() {
    document.querySelectorAll('.form-section').forEach(f => f.classList.remove('active'));
    document.getElementById('results').classList.remove('active');
}

function closeForm(formId) {
    document.getElementById(formId).classList.remove('active');
    if (formId === 'results') {
        document.getElementById('homeSection').classList.remove('hidden');
    }
}

function showProductAnalysis() {
    closeAllForms();
    document.getElementById('productAnalysisForm').classList.add('active');
    document.getElementById('productAnalysisForm').scrollIntoView({behavior: 'smooth'});
}

function showRecommendations() {
    closeAllForms();
    document.getElementById('recommendationForm').classList.add('active');
    document.getElementById('recommendationForm').scrollIntoView({behavior: 'smooth'});
}

function showAllergyCheck() {
    closeAllForms();
    document.getElementById('allergyCheckForm').classList.add('active');
    document.getElementById('allergyCheckForm').scrollIntoView({behavior: 'smooth'});
}

function resetForm() {
    closeAllForms();
    document.getElementById('homeSection').classList.remove('hidden');
}

function closeBanner() {
    document.getElementById('welcomeBanner').style.display = 'none';
}

// Sidebar Functions
function toggleSidebar() {
    document.getElementById('sidebar').classList.toggle('active');
    document.getElementById('sidebarOverlay').classList.toggle('active');
}

// Modal Functions
function showModal(type) {
    document.getElementById(type + 'Modal').classList.add('active');
}

function closeModal(type) {
    document.getElementById(type + 'Modal').classList.remove('active');
}

// Auth Functions
async function login(e) {
    e.preventDefault();
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    try {
        const res = await fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email, password})
        });
        const data = await res.json();
        
        if (data.success) {
            userToken = data.token;
            currentUser = data.user.id;
            localStorage.setItem('userToken', userToken);
            localStorage.setItem('userName', data.user.name);
            localStorage.setItem('userId', data.user.id);
            
            updateAuthUI(true, data.user.name);
            showSuccess(`Welcome back, ${data.user.name}!`);
            closeModal('login');
        } else {
            showError(data.error || 'Login failed');
        }
    } catch (err) {
        showError('Login failed. Please try again.');
    }
}

async function signup(e) {
    e.preventDefault();
    const name = document.getElementById('signupName').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    
    try {
        const res = await fetch(`${API_URL}/auth/signup`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({name, email, password})
        });
        const data = await res.json();
        
        if (data.success) {
            userToken = data.token;
            currentUser = data.user.id;
            localStorage.setItem('userToken', userToken);
            localStorage.setItem('userName', data.user.name);
            localStorage.setItem('userId', data.user.id);
            
            updateAuthUI(true, data.user.name);
            showSuccess(`Welcome, ${data.user.name}!`);
            closeModal('signup');
        } else {
            showError(data.error || 'Signup failed');
        }
    } catch (err) {
        showError('Signup failed. Please try again.');
    }
}

function logout() {
    userToken = null;
    currentUser = null;
    localStorage.removeItem('userToken');
    localStorage.removeItem('userName');
    localStorage.removeItem('userId');
    
    updateAuthUI(false);
    showSuccess('You have been logged out successfully.');
}

// Check for stored login on page load
function checkStoredLogin() {
    const storedToken = localStorage.getItem('userToken');
    const storedName = localStorage.getItem('userName');
    const storedId = localStorage.getItem('userId');
    
    if (storedToken && storedName && storedId) {
        userToken = storedToken;
        currentUser = storedId;
        updateAuthUI(true, storedName);
    }
}

// Initialize
window.addEventListener('load', () => {
    checkAPIHealth();
    checkStoredLogin();
});

// Exit Feedback
let feedbackGiven = false;
let userRating = 0;

function initStarRating() {
    const stars = document.querySelectorAll('.star');
    stars.forEach(star => {
        star.addEventListener('click', function() {
            userRating = parseInt(this.dataset.rating);
            document.getElementById('exitRating').value = userRating;
            
            stars.forEach((s, index) => {
                if (index < userRating) {
                    s.classList.add('active');
                } else {
                    s.classList.remove('active');
                }
            });
        });
    });
}

function showExitFeedback() {
    if (!feedbackGiven && !localStorage.getItem('feedbackGiven')) {
        document.getElementById('exitFeedbackModal').classList.add('active');
        initStarRating();
    }
}

async function submitExitFeedback(e) {
    e.preventDefault();
    
    const rating = document.getElementById('exitRating').value;
    const comments = document.getElementById('exitComments').value;
    
    try {
        // Save feedback (you can add API call here)
        console.log('Feedback:', { rating, comments, userId: currentUser });
        
        feedbackGiven = true;
        localStorage.setItem('feedbackGiven', 'true');
        
        showSuccess('Thank you for your feedback! 🙏');
        document.getElementById('exitFeedbackModal').classList.remove('active');
    } catch (err) {
        showError('Failed to submit feedback');
    }
}

function skipFeedback() {
    feedbackGiven = true;
    localStorage.setItem('feedbackGiven', 'true');
    document.getElementById('exitFeedbackModal').classList.remove('active');
}

// Show feedback on page unload or navigation away
window.addEventListener('beforeunload', function(e) {
    if (!feedbackGiven && !localStorage.getItem('feedbackGiven')) {
        showExitFeedback();
        e.preventDefault();
        e.returnValue = '';
    }
});

// Also show after 5 minutes of usage
setTimeout(() => {
    if (!feedbackGiven && !localStorage.getItem('feedbackGiven')) {
        showExitFeedback();
    }
}, 300000); // 5 minutes