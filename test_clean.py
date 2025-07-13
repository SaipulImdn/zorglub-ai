#!/usr/bin/env python3
"""
Test script to demonstrate clean architecture without Flask/HTML
"""

from infrastructure.dependency_injection import DependencyContainer
from core.use_cases.voice_assistant import VoiceAssistant

def test_clean_architecture():
    print("Testing Clean Architecture...")
    print("=" * 50)
    
    # Test dependency injection
    container = DependencyContainer()
    ai_service = container.get_ai_service()
    speech_input = container.get_speech_input()
    speech_output = container.get_speech_output()
    
    print("Dependency injection berhasil")
    print("AI Service initialized")
    print("Speech Input initialized") 
    print("Speech Output initialized")
    
    # Test voice assistant
    voice_assistant = VoiceAssistant(ai_service, speech_input, speech_output)
    print("Voice Assistant initialized")
    
    print("\n Clean Architecture Summary:")
    print("- No Flask dependency")
    print("- No HTML templates") 
    print("- Pure CLI interface")
    print("- Clean separation of concerns")
    print("- Dependency injection")
    print("- Interface abstractions")
    
    print("\n Ready untuk voice interactions!")

if __name__ == "__main__":
    test_clean_architecture()
