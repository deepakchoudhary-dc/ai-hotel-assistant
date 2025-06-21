"""
Voice service for handling speech-to-text and text-to-speech operations.
"""

import os
import io
import logging
import tempfile
from typing import Optional, BinaryIO

# Add FFmpeg to PATH if available
def add_ffmpeg_to_path():
    """Add FFmpeg to system PATH if found in common locations."""
    ffmpeg_paths = [
        r"C:\Users\mrrr7\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-7.1.1-full_build\bin",
        r"C:\ffmpeg\bin",
        r"C:\Program Files\ffmpeg\bin"
    ]
    
    for path in ffmpeg_paths:
        if os.path.exists(os.path.join(path, "ffmpeg.exe")):
            if path not in os.environ.get("PATH", ""):
                os.environ["PATH"] = path + os.pathsep + os.environ.get("PATH", "")
                logging.info(f"Added FFmpeg to PATH: {path}")
            return True
    return False

# Initialize FFmpeg PATH
add_ffmpeg_to_path()

# Optional imports for voice services
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    whisper = None

# TTS Options (in order of preference)
try:
    from elevenlabs import generate, save
    from elevenlabs.client import ElevenLabs
    ELEVENLABS_AVAILABLE = True
except ImportError:
    ELEVENLABS_AVAILABLE = False
    generate = None
    save = None
    ElevenLabs = None

try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    pyttsx3 = None

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    gTTS = None

logger = logging.getLogger(__name__)


class VoiceService:
    """Service for handling voice operations."""
    
    def __init__(self):
        """Initialize the voice service."""
        self.whisper_model = None
        self.elevenlabs_client = None
        self.pyttsx3_engine = None
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize speech services."""
        try:
            # Don't load Whisper model immediately - use lazy loading
            if WHISPER_AVAILABLE:
                logger.info("Whisper is available - will load model when needed")
                self.whisper_model = None  # Will be loaded on first use
            else:
                logger.warning("Whisper not available - speech-to-text will not work")
                self.whisper_model = None
            
            # Initialize TTS services (try in order of preference)
            tts_initialized = False
            
            # 1. Try ElevenLabs first (if API key is provided)
            elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
            if ELEVENLABS_AVAILABLE and elevenlabs_api_key:
                try:
                    self.elevenlabs_client = ElevenLabs(api_key=elevenlabs_api_key)
                    logger.info("ElevenLabs client initialized successfully")
                    tts_initialized = True
                except Exception as e:
                    logger.warning(f"Failed to initialize ElevenLabs: {e}")
                    self.elevenlabs_client = None
            else:
                self.elevenlabs_client = None
            
            # 2. Try pyttsx3 (offline, Windows built-in)
            if not tts_initialized and PYTTSX3_AVAILABLE:
                try:
                    self.pyttsx3_engine = pyttsx3.init()
                    # Configure voice settings
                    voices = self.pyttsx3_engine.getProperty('voices')
                    if voices:
                        # Try to find a female voice
                        for voice in voices:
                            if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                                self.pyttsx3_engine.setProperty('voice', voice.id)
                                break
                    
                    # Set speech rate and volume
                    self.pyttsx3_engine.setProperty('rate', 180)  # Speed of speech
                    self.pyttsx3_engine.setProperty('volume', 0.9)  # Volume level
                    
                    logger.info("pyttsx3 (Windows SAPI) TTS initialized successfully")
                    tts_initialized = True
                except Exception as e:
                    logger.warning(f"Failed to initialize pyttsx3: {e}")
                    self.pyttsx3_engine = None
            else:
                self.pyttsx3_engine = None
            
            if not tts_initialized:
                logger.warning("No TTS service available")
                
        except Exception as e:
            logger.error(f"Error initializing voice services: {str(e)}")
            self.whisper_model = None
            self.elevenlabs_client = None
            self.pyttsx3_engine = None
    
    def _load_whisper_model(self):
        """Lazy load Whisper model when needed."""
        if WHISPER_AVAILABLE and self.whisper_model is None:
            try:
                logger.info("Loading Whisper model...")
                self.whisper_model = whisper.load_model("base")
                logger.info("Whisper model loaded successfully")
                return True
            except Exception as e:
                logger.error(f"Failed to load Whisper model: {str(e)}")
                return False
        return self.whisper_model is not None
    
    async def speech_to_text(self, audio_data: bytes) -> Optional[str]:
        """
        Convert speech to text using Whisper.
        
        Args:
            audio_data: Audio file binary data
            
        Returns:
            Transcribed text or None if error
        """
        try:
            if not WHISPER_AVAILABLE:
                logger.error("Whisper not available")
                return None
                
            # Load Whisper model if not already loaded
            if self.whisper_model is None:
                logger.info("Loading Whisper model...")
                self.whisper_model = whisper.load_model("base")
                logger.info("Whisper model loaded successfully")
            
            # Save audio data temporarily with .wav extension
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Transcribe audio
                logger.info(f"Transcribing audio file: {temp_file_path}")
                logger.info(f"Audio file size: {len(audio_data)} bytes")
                
                # Try to transcribe with error handling for ffmpeg issues
                try:
                    result = self.whisper_model.transcribe(temp_file_path)
                    transcribed_text = result["text"].strip()
                    
                    logger.info(f"Transcription result: '{transcribed_text}'")
                    
                    if transcribed_text:
                        return transcribed_text
                    else:
                        logger.warning("Empty transcription result")
                        return None
                        
                except Exception as whisper_error:
                    error_str = str(whisper_error)
                    if "ffmpeg" in error_str.lower() or "file specified" in error_str.lower():
                        logger.error("FFmpeg not found - please install FFmpeg for voice recognition")
                        return "FFmpeg required for voice processing"
                    else:
                        logger.error(f"Whisper transcription error: {whisper_error}")
                        return None
                    
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception as e:
                    logger.warning(f"Could not delete temp file: {e}")
                    
        except Exception as e:
            logger.error(f"Error in speech-to-text: {str(e)}")
            return None
            
            try:
                # Transcribe audio
                logger.info("Transcribing audio...")
                result = self.whisper_model.transcribe(temp_file_path)
                transcribed_text = result["text"].strip()
                
                logger.info(f"Transcription successful: {transcribed_text[:100]}...")
                return transcribed_text
                
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            logger.error(f"Error in speech-to-text conversion: {str(e)}")
            return None
    
    async def text_to_speech(self, text: str) -> Optional[bytes]:
        """
        Convert text to speech using available TTS services.
        
        Args:
            text: Text to convert to speech
            
        Returns:
            Audio bytes or None if error
        """
        try:
            if not text or not text.strip():
                logger.warning("Empty text provided for TTS")
                return None
            
            logger.info(f"Generating speech for text: {text[:100]}...")
            
            # Try ElevenLabs first (best quality)
            if ELEVENLABS_AVAILABLE and self.elevenlabs_client:
                try:
                    audio = generate(
                        text=text,
                        voice="Rachel",
                        model="eleven_monolingual_v1"
                    )
                    logger.info("Speech generation successful using ElevenLabs")
                    return audio
                except Exception as e:
                    logger.warning(f"ElevenLabs TTS failed: {e}")
            
            # Try pyttsx3 (Windows SAPI)
            if PYTTSX3_AVAILABLE and self.pyttsx3_engine:
                try:
                    # Save to temporary file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as temp_file:
                        temp_file_path = temp_file.name
                    
                    # Generate speech
                    self.pyttsx3_engine.save_to_file(text, temp_file_path)
                    self.pyttsx3_engine.runAndWait()
                    
                    # Read the generated file
                    with open(temp_file_path, 'rb') as f:
                        audio_data = f.read()
                    
                    # Clean up
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                    
                    logger.info("Speech generation successful using pyttsx3")
                    return audio_data
                    
                except Exception as e:
                    logger.warning(f"pyttsx3 TTS failed: {e}")
            
            # Try gTTS (Google TTS) - requires internet
            if GTTS_AVAILABLE:
                try:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_file:
                        temp_file_path = temp_file.name
                    
                    # Generate speech
                    tts = gTTS(text=text, lang='en', slow=False)
                    tts.save(temp_file_path)
                    
                    # Read the generated file
                    with open(temp_file_path, 'rb') as f:
                        audio_data = f.read()
                    
                    # Clean up
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                    
                    logger.info("Speech generation successful using gTTS")
                    return audio_data
                    
                except Exception as e:
                    logger.warning(f"gTTS failed: {e}")
            
            logger.error("No TTS service available")
            return None
            
        except Exception as e:
            logger.error(f"Error in text-to-speech conversion: {str(e)}")
            return None
    
    async def process_voice_message(
        self, 
        audio_file: bytes,
        conversation_service,
        session_id: str,
        db_session,
        guest_id: Optional[int] = None
    ) -> dict:
        """
        Process a voice message end-to-end.
        
        Args:
            audio_file: Input audio file
            conversation_service: Conversation service instance
            session_id: Session ID for conversation
            db_session: Database session
            guest_id: Optional guest ID
            
        Returns:
            Dictionary with transcription, response text, and audio response
        """
        try:            # Convert speech to text
            transcribed_text = await self.speech_to_text(audio_file)
            if not transcribed_text:
                # Return error if transcription fails
                return {
                    "error": "Could not transcribe audio - please try again or speak more clearly",
                    "transcription": None,
                    "response_text": None,
                    "response_audio": None
                }
            
            # Process the message through conversation service
            conversation_result = await conversation_service.process_message(
                message=transcribed_text,
                session_id=session_id,
                db=db_session,
                guest_id=guest_id
            )
            
            response_text = conversation_result.get("response", "")
            
            # Convert response to speech
            response_audio = await self.text_to_speech(response_text)
            
            return {
                "transcription": transcribed_text,
                "response_text": response_text,
                "response_audio": response_audio,
                "intent": conversation_result.get("intent"),
                "session_id": session_id,
                "timestamp": conversation_result.get("timestamp")            }
            
        except Exception as e:
            logger.error(f"Error processing voice message: {str(e)}")
            return {
                "error": f"Error processing voice message: {str(e)}",
                "transcription": None,
                "response_text": None,
                "response_audio": None
            }
    
    def is_tts_available(self) -> bool:
        """Check if text-to-speech is available."""
        return (ELEVENLABS_AVAILABLE and self.elevenlabs_client is not None) or \
               PYTTSX3_AVAILABLE or GTTS_AVAILABLE
    
    def is_stt_available(self) -> bool:
        """Check if speech-to-text is available."""
        if WHISPER_AVAILABLE:
            self._load_whisper_model()
            return self.whisper_model is not None
        return False
