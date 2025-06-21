# 🏨 Hotel AI Front Desk Assistant

A full-stack conversational AI system for hotel operations with voice and text interactions. Built with FastAPI, Ollama (Qwen3:1.7b), Whisper, and modern web technologies.

## ✨ Features

- 🗣️ **Voice & Text Chat**: Complete speech-to-text and audio responses
- 🤖 **Local AI**: Powered by Ollama with Qwen3:1.7b (no API keys required)
- 🏨 **Hotel Operations**: Room booking, check-in/out, amenities, recommendations
- 📱 **Modern Web UI**: Responsive interface with real-time voice indicators
- 💾 **Persistent Storage**: SQLite database for guests and conversations

## 🚀 Tech Stack

**Backend**: FastAPI, Ollama, Whisper, FFmpeg, SQLAlchemy, SQLite  
**Frontend**: HTML5/CSS3, JavaScript, Web Audio API, Font Awesome  
**AI Services**: Qwen3:1.7b, OpenAI Whisper, ElevenLabs/pyttsx3/gTTS

## 📁 Project Structure

```
hotel-ai-assistant/
├── backend/                 # FastAPI backend
│   ├── main.py             # Server entry point
│   ├── api/                # API routes
│   ├── services/           # Business logic
│   └── models/             # Database models
├── frontend/               # Web interface
│   ├── index.html          # Main UI
│   ├── styles.css          # Styling
│   └── app.js              # Frontend logic
├── data/                   # Hotel configuration
├── tests/                  # Test suite
├── requirements.txt        # Dependencies
└── README.md              # Documentation
```

## 🛠️ Quick Setup

### Prerequisites
- Python 3.8+, FFmpeg, Git
- Ollama with Qwen3:1.7b model

### Installation
```bash
# 1. Clone and setup
git clone <repo-url>
cd hotel-ai-assistant
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt

# 2. Install Ollama & model
winget install Ollama.Ollama   # Windows
ollama pull qwen3:1.7b

# 3. Install FFmpeg
winget install Gyan.FFmpeg     # Windows

# 4. Start services
ollama serve                   # Terminal 1
python backend/main.py         # Terminal 2

# 5. Open browser
# http://localhost:8000
```

## 🎯 Usage

### Web Interface
- **Text**: Type messages in chat input
- **Voice**: Click microphone, speak, release
- **Quick Actions**: Use preset buttons for common requests

### Voice Commands
- *"Book a room for tonight"*
- *"What's the WiFi password?"*
- *"Recommend nearby restaurants"*
- *"Pool hours?"*

## 🔧 API Endpoints

```http
POST /api/chat              # Text conversation
POST /api/voice             # Voice processing
GET  /api/rooms             # Room availability
POST /api/booking           # Create booking
GET  /docs                  # API documentation
```

## 🧪 Development

```bash
# Run tests
pytest tests/

# Start development server
uvicorn backend.main:app --reload

# Code formatting
black backend/
```

## 🚀 Deployment

### Docker
```bash
docker build -t hotel-ai .
docker run -p 8000:8000 hotel-ai
```

### Cloud Options
- Railway/Render (backend)
- Netlify/Vercel (frontend)
- AWS/GCP (full-stack)

## 🆘 Troubleshooting

**Voice not working?**
- Install FFmpeg: `winget install Gyan.FFmpeg`
- Check browser microphone permissions

**AI not responding?**
- Start Ollama: `ollama serve`
- Pull model: `ollama pull qwen3:1.7b`

## 🤝 Contributing

1. Fork repository
2. Create feature branch
3. Add tests
4. Submit pull request

## 📝 License

MIT License

---

**Built with ❤️ for hospitality**
