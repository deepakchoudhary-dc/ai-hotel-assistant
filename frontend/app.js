/**
 * Hotel AI Front Desk Assistant - Frontend JavaScript
 */

class HotelAssistant {
    constructor() {
        this.apiUrl = 'http://localhost:8000/api';
        this.sessionId = this.generateSessionId();
        this.isRecording = false;
        this.mediaRecorder = null;
        this.audioChunks = [];
        this.isVoiceAvailable = false;
        
        this.initializeElements();
        this.attachEventListeners();
        this.checkVoiceCapabilities();
    }
    
    initializeElements() {
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.voiceButton = document.getElementById('voiceButton');
        this.voiceIndicator = document.getElementById('voiceIndicator');
        this.chatMessages = document.getElementById('chatMessages');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.audioPlayer = document.getElementById('audioPlayer');
        this.textStatus = document.getElementById('text-status');
        this.voiceStatus = document.getElementById('voice-status');
        this.actionButtons = document.querySelectorAll('.action-button');
    }
    
    attachEventListeners() {
        // Text input events
        this.messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });
        
        this.sendButton.addEventListener('click', () => this.sendMessage());
        
        // Voice events
        this.voiceButton.addEventListener('mousedown', () => this.startRecording());
        this.voiceButton.addEventListener('mouseup', () => this.stopRecording());
        this.voiceButton.addEventListener('mouseleave', () => this.stopRecording());
        
        // Touch events for mobile
        this.voiceButton.addEventListener('touchstart', (e) => {
            e.preventDefault();
            this.startRecording();
        });
        this.voiceButton.addEventListener('touchend', (e) => {
            e.preventDefault();
            this.stopRecording();
        });
        
        // Quick action buttons
        this.actionButtons.forEach(button => {
            button.addEventListener('click', () => {
                const message = button.getAttribute('data-message');
                this.messageInput.value = message;
                this.sendMessage();
            });
        });
    }
    
    generateSessionId() {
        return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    }
    
    async checkVoiceCapabilities() {
        try {
            const response = await fetch(`${this.apiUrl}/voice/capabilities`);
            const capabilities = await response.json();
            
            this.isVoiceAvailable = capabilities.speech_to_text;
            
            if (this.isVoiceAvailable) {
                this.voiceButton.disabled = false;
                this.voiceStatus.innerHTML = '<i class="fas fa-microphone"></i> Voice: Ready';
                this.voiceStatus.classList.remove('disabled');
            } else {
                this.voiceButton.disabled = true;
                this.voiceStatus.innerHTML = '<i class="fas fa-microphone-slash"></i> Voice: Unavailable';
                this.voiceStatus.classList.add('disabled');
            }
            
            // Check for microphone permission
            if (this.isVoiceAvailable) {
                await this.initializeMicrophone();
            }
            
        } catch (error) {
            console.error('Error checking voice capabilities:', error);
            this.voiceButton.disabled = true;
            this.voiceStatus.innerHTML = '<i class="fas fa-microphone-slash"></i> Voice: Error';
            this.voiceStatus.classList.add('disabled');
        }
    }
    
    async initializeMicrophone() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            stream.getTracks().forEach(track => track.stop()); // Stop the stream immediately
            console.log('Microphone access granted');
        } catch (error) {
            console.error('Microphone access denied:', error);
            this.voiceButton.disabled = true;
            this.voiceStatus.innerHTML = '<i class="fas fa-microphone-slash"></i> Voice: Mic Denied';
            this.voiceStatus.classList.add('disabled');
        }
    }
    
    async sendMessage() {
        const message = this.messageInput.value.trim();
        if (!message) return;
        
        // Clear input and show user message
        this.messageInput.value = '';
        this.addMessage(message, 'user');
        
        // Show loading
        this.showLoading(true);
        this.sendButton.disabled = true;
        
        try {
            const response = await fetch(`${this.apiUrl}/chat`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    session_id: this.sessionId
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            this.addMessage(data.response, 'assistant');
            
            // Try to get audio response if available
            await this.getAudioResponse(data.response);
            
        } catch (error) {
            console.error('Error sending message:', error);
            this.addMessage('I apologize, but I\'m having trouble connecting to the server. Please try again or speak with our front desk staff.', 'assistant');
        } finally {
            this.showLoading(false);
            this.sendButton.disabled = false;
            this.messageInput.focus();
        }
    }
    
    async getAudioResponse(text) {
        try {
            const response = await fetch(`${this.apiUrl}/text-to-speech`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `text=${encodeURIComponent(text)}`
            });
            
            if (response.ok) {
                const audioBlob = await response.blob();
                const audioUrl = URL.createObjectURL(audioBlob);
                this.audioPlayer.src = audioUrl;
                
                // Add play button to the last message
                const lastMessage = this.chatMessages.lastElementChild;
                if (lastMessage && lastMessage.classList.contains('assistant-message')) {
                    const playButton = document.createElement('button');
                    playButton.className = 'play-audio-button';
                    playButton.innerHTML = '<i class="fas fa-play"></i> Play Audio';
                    playButton.onclick = () => {
                        this.audioPlayer.play();
                        playButton.innerHTML = '<i class="fas fa-volume-up"></i> Playing...';
                        
                        this.audioPlayer.onended = () => {
                            playButton.innerHTML = '<i class="fas fa-play"></i> Play Audio';
                        };
                    };
                    
                    const messageContent = lastMessage.querySelector('.message-content');
                    messageContent.appendChild(playButton);
                }
            }
        } catch (error) {
            console.error('Error getting audio response:', error);
        }
    }
    
    async startRecording() {
        if (!this.isVoiceAvailable || this.isRecording) return;
        
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            
            this.mediaRecorder = new MediaRecorder(stream);
            this.audioChunks = [];
            this.isRecording = true;
            
            this.mediaRecorder.ondataavailable = (event) => {
                this.audioChunks.push(event.data);
            };
            
            this.mediaRecorder.onstop = () => {
                this.processVoiceMessage();
            };
            
            this.mediaRecorder.start();
            
            // Update UI
            this.voiceButton.classList.add('recording');
            this.voiceButton.innerHTML = '<i class="fas fa-stop"></i> <span>Release to Send</span>';
            this.voiceIndicator.classList.add('active');
            
        } catch (error) {
            console.error('Error starting recording:', error);
            this.addMessage('Sorry, I couldn\'t access your microphone. Please check your browser permissions.', 'assistant');
        }
    }
    
    stopRecording() {
        if (!this.isRecording || !this.mediaRecorder) return;
        
        this.mediaRecorder.stop();
        this.mediaRecorder.stream.getTracks().forEach(track => track.stop());
        
        this.isRecording = false;
        
        // Update UI
        this.voiceButton.classList.remove('recording');
        this.voiceButton.innerHTML = '<i class="fas fa-microphone"></i> <span>Hold to Speak</span>';
        this.voiceIndicator.classList.remove('active');
    }
    
    async processVoiceMessage() {
        if (this.audioChunks.length === 0) return;
        
        // Create audio blob
        const audioBlob = new Blob(this.audioChunks, { type: 'audio/wav' });
        
        // Show loading
        this.showLoading(true);
        this.voiceButton.disabled = true;
        
        try {
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.wav');
            formData.append('session_id', this.sessionId);
            
            const response = await fetch(`${this.apiUrl}/voice`, {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
              // Show transcription as user message
            if (data.transcription) {
                this.addMessage(data.transcription, 'user');
            }
            
            // Show AI response
            if (data.response_text) {
                this.addMessage(data.response_text, 'assistant');
                
                // Add play button for audio response if available
                if (data.response_audio) {
                    const lastMessage = this.chatMessages.lastElementChild;
                    if (lastMessage && lastMessage.classList.contains('assistant-message')) {
                        const audioData = atob(data.response_audio);
                        const audioArray = new Uint8Array(audioData.length);
                        for (let i = 0; i < audioData.length; i++) {
                            audioArray[i] = audioData.charCodeAt(i);
                        }
                        const audioBlob = new Blob([audioArray], { type: 'audio/mpeg' });
                        const audioUrl = URL.createObjectURL(audioBlob);
                        
                        const playButton = document.createElement('button');
                        playButton.className = 'play-audio-button';
                        playButton.innerHTML = '<i class="fas fa-play"></i> Play Audio';
                        playButton.onclick = () => {
                            this.audioPlayer.src = audioUrl;
                            this.audioPlayer.play();
                            playButton.innerHTML = '<i class="fas fa-volume-up"></i> Playing...';
                            
                            this.audioPlayer.onended = () => {
                                playButton.innerHTML = '<i class="fas fa-play"></i> Play Audio';
                            };
                        };
                        
                        const messageContent = lastMessage.querySelector('.message-content');
                        messageContent.appendChild(playButton);
                    }
                }
            }} catch (error) {
            console.error('Error processing voice message:', error);
            this.addMessage('Sorry, there was an error processing your voice message. Please try again or type your message.', 'assistant');
        } finally {
            this.showLoading(false);
            this.voiceButton.disabled = false;
        }
    }
    
    addMessage(text, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        avatarDiv.innerHTML = sender === 'user' ? '<i class="fas fa-user"></i>' : '<i class="fas fa-robot"></i>';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Convert text to HTML, preserving line breaks and formatting
        const formattedText = text.replace(/\n/g, '<br>');
        contentDiv.innerHTML = `<p>${formattedText}</p>`;
        
        messageDiv.appendChild(avatarDiv);
        messageDiv.appendChild(contentDiv);
        
        this.chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }
    
    showLoading(show) {
        if (show) {
            this.loadingOverlay.classList.add('active');
        } else {
            this.loadingOverlay.classList.remove('active');
        }
    }
}

// Add CSS for play button
const playButtonStyle = document.createElement('style');
playButtonStyle.textContent = `
    .play-audio-button {
        margin-top: 10px;
        padding: 8px 16px;
        background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        color: white;
        border: none;
        border-radius: 20px;
        cursor: pointer;
        font-size: 0.9rem;
        transition: all 0.3s ease;
    }
    
    .play-audio-button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
    }
    
    .user-message .play-audio-button {
        background: rgba(255, 255, 255, 0.2);
        color: white;
    }
`;
document.head.appendChild(playButtonStyle);

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new HotelAssistant();
});
