/**
 * FundBot - HDFC Mutual Fund Chatbot Frontend
 * Modern chatbot interface with enhanced UX
 */

// Global state
let sessionId = null;
let isLoading = false;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    initializeSession();
    setupEventListeners();
});

/**
 * Initialize or restore session
 */
function initializeSession() {
    const storedSessionId = localStorage.getItem('rag_session_id');
    
    if (storedSessionId) {
        sessionId = storedSessionId;
    } else {
        sessionId = generateSessionId();
        localStorage.setItem('rag_session_id', sessionId);
    }
    
    // Display truncated session ID
    const displayId = sessionId.substring(0, 8) + '...';
    document.getElementById('sessionId').textContent = displayId;
    
    // Load conversation history
    loadHistory();
}

/**
 * Generate unique session ID
 */
function generateSessionId() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16);
    });
}

/**
 * Setup event listeners
 */
function setupEventListeners() {
    const input = document.getElementById('messageInput');
    
    // Character count
    input.addEventListener('input', () => {
        const count = input.value.length;
        const counter = document.getElementById('charCount');
        counter.textContent = `${count}/500`;
        
        if (count > 500) {
            counter.classList.add('warning');
        } else {
            counter.classList.remove('warning');
        }
    });
}

/**
 * Toggle quick questions sidebar
 */
function toggleSidebar() {
    const sidebar = document.getElementById('quickSidebar');
    sidebar.classList.toggle('active');
}

/**
 * Handle Enter key press
 */
function handleKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendMessage();
    }
}

/**
 * Send message to backend
 */
async function sendMessage() {
    const input = document.getElementById('messageInput');
    const message = input.value.trim();
    
    if (!message || isLoading) return;
    if (message.length > 500) {
        alert('Message too long. Maximum 500 characters allowed.');
        return;
    }
    if (message.length < 10) {
        alert('Message too short. Minimum 10 characters required.');
        return;
    }
    
    // Clear input
    input.value = '';
    document.getElementById('charCount').textContent = '0/500';
    
    // Add user message to UI
    addMessage(message, 'user');
    
    // Show loading
    setLoading(true);
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                message: message,
                session_id: sessionId
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // Update session ID if server created new one
            if (data.session_id && data.session_id !== sessionId) {
                sessionId = data.session_id;
                localStorage.setItem('rag_session_id', sessionId);
            }
            
            // Determine message type based on content
            let messageType = 'assistant';
            const responseText = data.response.toLowerCase();
            
            if (responseText.includes('not authorized') || 
                responseText.includes('cannot provide') ||
                responseText.includes('investment advice')) {
                messageType = 'refusal';
            } else if (responseText.includes('error') || responseText.includes('blocked')) {
                messageType = 'error';
            } else if (responseText.includes('source:') || responseText.includes('₹')) {
                messageType = 'factual';
            }
            
            addMessage(data.response, 'assistant', messageType);
        } else {
            addMessage(`Error: ${data.error || 'Something went wrong'}`, 'assistant', 'error');
        }
    } catch (error) {
        console.error('Error:', error);
        addMessage('Error: Failed to connect to the server. Please try again.', 'assistant', 'error');
    } finally {
        setLoading(false);
        scrollToBottom();
    }
}

/**
 * Add message to chat UI
 */
function addMessage(content, role, type = '') {
    const messagesDiv = document.getElementById('chatMessages');
    const welcomeSection = document.getElementById('welcomeSection');
    const chatContainer = document.getElementById('chatContainer');
    
    // Show chat container, hide welcome section when first message is sent
    if (role === 'user' && welcomeSection && chatContainer) {
        welcomeSection.style.display = 'none';
        chatContainer.style.display = 'block';
        chatContainer.classList.add('active');
    }
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message ${type}`;
    
    // Convert markdown-style bold to HTML
    const formattedContent = content
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>');
    
    // Determine avatar based on role
    const avatar = role === 'user' ? '🙂' : '🤖';
    
    messageDiv.innerHTML = `
        <div class="message-avatar">${avatar}</div>
        <div class="message-content">${formattedContent}</div>
    `;
    
    messagesDiv.appendChild(messageDiv);
    scrollToBottom();
}

/**
 * Quick question button handler
 */
function askQuestion(question) {
    document.getElementById('messageInput').value = question;
    document.getElementById('charCount').textContent = `${question.length}/500`;
    sendMessage();
}

/**
 * Clear chat history
 */
async function clearChat() {
    if (!confirm('Are you sure you want to clear this conversation?')) {
        return;
    }
    
    try {
        const response = await fetch('/api/clear', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                session_id: sessionId
            })
        });
        
        if (response.ok) {
            // Clear UI - reset to welcome screen
            const messagesDiv = document.getElementById('chatMessages');
            const welcomeSection = document.getElementById('welcomeSection');
            const chatContainer = document.getElementById('chatContainer');
            
            messagesDiv.innerHTML = '';
            
            // Show welcome section, hide chat container
            if (welcomeSection) welcomeSection.style.display = 'block';
            if (chatContainer) {
                chatContainer.style.display = 'none';
                chatContainer.classList.remove('active');
            }
            
            // Generate new session
            sessionId = generateSessionId();
            localStorage.setItem('rag_session_id', sessionId);
            document.getElementById('sessionId').textContent = sessionId.substring(0, 8) + '...';
            
            // Reset character count
            document.getElementById('charCount').textContent = '0/500';
            document.getElementById('charCount').classList.remove('warning');
        } else {
            alert('Failed to clear conversation.');
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error clearing conversation.');
    }
}

/**
 * Export chat
 */
async function exportChat() {
    try {
        const response = await fetch(`/api/export?session_id=${sessionId}&format=markdown`);
        const data = await response.json();
        
        if (response.ok) {
            alert(`Chat exported successfully!\nFile: ${data.filepath}`);
        } else {
            alert(`Export failed: ${data.error}`);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Error exporting chat.');
    }
}

/**
 * Load conversation history
 */
async function loadHistory() {
    try {
        const response = await fetch(`/api/history?session_id=${sessionId}&limit=10`);
        const data = await response.json();
        
        if (response.ok && data.history && data.history.length > 0) {
            // Hide welcome section, show chat container
            const welcomeSection = document.getElementById('welcomeSection');
            const chatContainer = document.getElementById('chatContainer');
            
            if (welcomeSection) welcomeSection.style.display = 'none';
            if (chatContainer) {
                chatContainer.style.display = 'block';
                chatContainer.classList.add('active');
            }
            
            // Display history
            data.history.forEach(msg => {
                let type = '';
                if (msg.role === 'assistant') {
                    const content = msg.content.toLowerCase();
                    if (content.includes('not authorized') || content.includes('cannot provide')) {
                        type = 'refusal';
                    } else if (content.includes('error')) {
                        type = 'error';
                    } else if (content.includes('source:')) {
                        type = 'factual';
                    }
                }
                
                addMessage(msg.content, msg.role, type);
            });
        }
    } catch (error) {
        console.log('No history to load or error:', error);
    }
}

/**
 * Set loading state - shows typing indicator
 */
function setLoading(loading) {
    isLoading = loading;
    const indicator = document.getElementById('typingIndicator');
    
    if (loading) {
        indicator.style.display = 'flex';
        scrollToBottom();
    } else {
        indicator.style.display = 'none';
    }
}

/**
 * Scroll messages to bottom
 */
function scrollToBottom() {
    const messagesDiv = document.getElementById('chatMessages');
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}
