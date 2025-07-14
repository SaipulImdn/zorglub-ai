import os
from typing import Optional
from core.interfaces.ai_service import AIServiceInterface
from core.interfaces.speech_input import SpeechInputInterface
from core.interfaces.speech_output import SpeechOutputInterface
from core.conversation_manager import ConversationManager

# Import both regular dan multiprocess factories
from .factories.ai_factory import get_ai_client
from .factories.speech_factory import get_stt_service
from .factories.audio_factory import get_tts_service

# Import multiprocess factories
from .factories.multiprocess_ai_factory import get_multiprocess_ai_client
from .factories.multiprocess_speech_factory import get_multiprocess_stt_service
from .factories.multiprocess_audio_factory import get_multiprocess_tts_service

import os

class AIServiceAdapter(AIServiceInterface):
    def __init__(self, use_multiprocess: bool = True):
        self._client = None
        self._use_multiprocess = use_multiprocess
        self._is_main_process = os.getpid() == os.getppid() if hasattr(os, 'getppid') else True
    
    @property
    def client(self):
        import logging
        if self._client is None:
            if self._use_multiprocess and self._is_main_process:
                try:
                    self._client = get_multiprocess_ai_client()
                except Exception as e:
                    try:
                        logging.warning(f"Multiprocess client failed, falling back to regular: {e}")
                    except Exception:
                        pass
                    self._client = get_ai_client()
            else:
                self._client = get_ai_client()
        return self._client
    
    def ask(self, prompt: str) -> str:
        return self.client.ask(prompt)
    
    def ask_with_context(self, prompt: str, conversation_manager: ConversationManager) -> str:
        # Get context-enhanced prompt
        context_prompt = conversation_manager.get_context_prompt(prompt)
        
        # Convert context to messages format
        messages = [{"role": "user", "content": context_prompt}]
        
        # Add conversation history untuk better context
        history = conversation_manager.get_conversation_history()
        if history:
            messages = []
            for msg in history[-5:]:  # Last 5 messages untuk context
                role = "user" if msg.role == "user" else "assistant"
                messages.append({"role": role, "content": msg.content})
            
            # Add current prompt
            messages.append({"role": "user", "content": prompt})
        
        # Enhanced options untuk conversational AI
        options = {
            "temperature": 0.7,
            "top_p": 0.9,
            "num_ctx": 4096,
            "repeat_penalty": 1.1
        }
        
        # Get AI response
        response = self.client.ask_with_context(messages, options=options)
        
        # Add to conversation history
        context_tags = conversation_manager._detect_context(prompt)
        conversation_manager.add_message('user', prompt, context_tags)
        conversation_manager.add_message('assistant', response)
        
        return response
    
    def ask_batch(self, prompts: list, use_cache: bool = True) -> list:
        if hasattr(self.client, 'ask_batch'):
            return self.client.ask_batch(prompts, use_cache=use_cache)
        else:
            # Fallback untuk regular client
            return [self.ask(prompt) for prompt in prompts]

class SpeechToTextAdapter(SpeechInputInterface):
    def __init__(self, use_multiprocess: bool = True):
        self._service = None
        self._use_multiprocess = use_multiprocess
        self._is_main_process = os.getpid() == os.getppid() if hasattr(os, 'getppid') else True
    
    @property
    def service(self):
        import logging
        if self._service is None:
            if self._use_multiprocess and self._is_main_process:
                try:
                    self._service = get_multiprocess_stt_service()
                except Exception as e:
                    try:
                        logging.warning(f"Multiprocess STT failed, falling back to regular: {e}")
                    except Exception:
                        pass
                    self._service = get_stt_service()
            else:
                self._service = get_stt_service()
        return self._service
    
    def listen(self) -> Optional[str]:
        return self.service.listen()
    
    def transcribe_file(self, audio_file: str) -> Optional[str]:
        return self.service.transcribe_audio(audio_file)
    
    def transcribe_batch(self, audio_files: list) -> list:
        if hasattr(self.service, 'transcribe_batch'):
            return self.service.transcribe_batch(audio_files)
        else:
            return [self.transcribe_file(f) for f in audio_files]
    
    def listen_batch(self, count: int) -> list:
        if hasattr(self.service, 'listen_batch'):
            return self.service.listen_batch(count)
        else:
            return [self.listen() for _ in range(count)]

class TextToSpeechAdapter(SpeechOutputInterface): 
    def __init__(self, use_multiprocess: bool = True):
        self._service = None
        self._use_multiprocess = use_multiprocess
        self._is_main_process = os.getpid() == os.getppid() if hasattr(os, 'getppid') else True
    
    @property
    def service(self):
        import logging
        if self._service is None:
            if self._use_multiprocess and self._is_main_process:
                try:
                    self._service = get_multiprocess_tts_service()
                except Exception as e:
                    try:
                        logging.warning(f"Multiprocess TTS failed, falling back to regular: {e}")
                    except Exception:
                        pass
                    self._service = get_tts_service()
            else:
                self._service = get_tts_service()
        return self._service
    
    def speak(self, text: str, engine: str = None) -> bool:
        return self.service.speak(text, engine=engine)
    
    def speak_async(self, text: str, engine: str = None) -> bool:
        if hasattr(self.service, 'speak'):
            return self.service.speak(text, engine=engine, parallel_mode=True)
        else:
            return self.service.speak(text, engine=engine)
    
    def speak_batch(self, texts: list, engine: str = None) -> list:
        if hasattr(self.service, 'speak_batch'):
            return self.service.speak_batch(texts, engine=engine)
        else:
            return [self.speak(text, engine) for text in texts]

# Backward compatibility functions
def get_enhanced_ai_service(use_multiprocess: bool = True) -> AIServiceAdapter:
    """Get enhanced AI service adapter"""
    return AIServiceAdapter(use_multiprocess=use_multiprocess)

def get_enhanced_stt_service(use_multiprocess: bool = True) -> SpeechToTextAdapter:
    """Get enhanced STT service adapter"""
    return SpeechToTextAdapter(use_multiprocess=use_multiprocess)

def get_enhanced_tts_service(use_multiprocess: bool = True) -> TextToSpeechAdapter:
    """Get enhanced TTS service adapter"""
    return TextToSpeechAdapter(use_multiprocess=use_multiprocess)

def patch_original_interfaces():
    from core.interfaces import ai_service, speech_input, speech_output
    
    # Replace dengan enhanced adapters
    ai_service.AIService = lambda: AIServiceAdapter(use_multiprocess=True)
    speech_input.SpeechToText = lambda: SpeechToTextAdapter(use_multiprocess=True)
    speech_output.TextToSpeech = lambda: TextToSpeechAdapter(use_multiprocess=True)
    
    print("Patched interfaces dengan enhanced multiprocess implementations")

# Auto-patch saat module di-import
patch_original_interfaces()

# Convenience functions for getting enhanced services
def get_enhanced_ai_service(use_multiprocess: bool = True) -> AIServiceAdapter:
    """Get enhanced AI service adapter"""
    return AIServiceAdapter(use_multiprocess=use_multiprocess)

def get_enhanced_stt_service(use_multiprocess: bool = True) -> SpeechToTextAdapter:
    """Get enhanced STT service adapter"""
    return SpeechToTextAdapter(use_multiprocess=use_multiprocess)

def get_enhanced_tts_service(use_multiprocess: bool = True) -> TextToSpeechAdapter:
    """Get enhanced TTS service adapter"""
    return TextToSpeechAdapter(use_multiprocess=use_multiprocess)
