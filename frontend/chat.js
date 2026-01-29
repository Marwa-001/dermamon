// Chat Functions
// Chat Functions
function toggleChat() {
    const chatWindow = document.getElementById('chatWindow');
    const chatWidget = document.getElementById('chatWidget');
    
    chatWindow.classList.toggle('active');
    
    // Hide the widget when chat is open
    if (chatWindow.classList.contains('active')) {
        chatWidget.style.display = 'none';
    } else {
        chatWidget.style.display = 'block';
    }
}

async function sendMessage() {
    const input = document.getElementById('chatInput');
    const msg = input.value.trim();
    if (!msg) return;
    
    addChatMessage(msg, 'user');
    input.value = '';
    
    // Show typing indicator
    addTypingIndicator();
    
    try {
        const res = await fetch(`${API_URL}/chat`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                message: msg, 
                user_id: currentUser || 'guest'
            })
        });
        const data = await res.json();
        
        removeTypingIndicator();
        
        if (data.success) {
            addChatMessage(data.response, 'bot');
        } else {
            addChatMessage('Sorry, I encountered an error. Please try again!', 'bot');
        }
    } catch {
        removeTypingIndicator();
        addChatMessage('Sorry, I\'m having trouble connecting. Please try again!', 'bot');
    }
}

function addChatMessage(text, sender) {
    const div = document.createElement('div');
    div.className = `chat-message ${sender}`;
    div.innerHTML = `<div class="message-bubble ${sender}">${text}</div>`;
    
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addTypingIndicator() {
    const div = document.createElement('div');
    div.className = 'chat-message bot typing-indicator';
    div.id = 'typingIndicator';
    div.innerHTML = `<div class="message-bubble bot">
        <span class="dot"></span><span class="dot"></span><span class="dot"></span>
    </div>`;
    
    const messagesContainer = document.getElementById('chatMessages');
    messagesContainer.appendChild(div);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function removeTypingIndicator() {
    const indicator = document.getElementById('typingIndicator');
    if (indicator) {
        indicator.remove();
    }
}

// Add typing indicator animation to CSS dynamically
const style = document.createElement('style');
style.textContent = `
.typing-indicator .message-bubble {
    display: flex;
    gap: 4px;
    padding: 0.75rem 1rem;
}

.typing-indicator .dot {
    width: 8px;
    height: 8px;
    background: var(--text-light);
    border-radius: 50%;
    animation: typingDot 1.4s infinite;
}

.typing-indicator .dot:nth-child(2) {
    animation-delay: 0.2s;
}

.typing-indicator .dot:nth-child(3) {
    animation-delay: 0.4s;
}

@keyframes typingDot {
    0%, 60%, 100% {
        opacity: 0.3;
        transform: translateY(0);
    }
    30% {
        opacity: 1;
        transform: translateY(-10px);
    }
}
`;
document.head.appendChild(style);