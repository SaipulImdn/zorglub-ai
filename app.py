#!/usr/bin/env python3
"""
Zorglub AI - Main Application Entry Point
Clean Architecture with app.py as the main gateway
"""


import sys
import os
from core.use_cases.voice_assistant import VoiceAssistant
from infrastructure.dependency_injection import DependencyContainer
from shared.config import Config

def show_banner():
    """Show welcome banner"""
    print("=" * 60)
    print("ZORGLUB AI - Voice Assistant")
    print("=" * 60)
    print("Modes:")
    print("  1. Single Voice - One recording, one response")
    print("  2. Text Chat    - Type your questions")
    print("  3. Voice Chat   - Continuous voice conversation")
    print("=" * 60)
    print(f"AI Model: {Config.OLLAMA_MODEL}")
    print("=" * 60)

def show_help():
    """Show available command line options"""
    print("\nUsage:")
    print("  python app.py           - Interactive mode")
    print("  python app.py --single  - Single voice interaction")
    print("  python app.py --text    - Text chat mode")
    print("  python app.py --voice   - Voice chat mode")
    print("  python app.py --check   - Check dependencies")
    print("  python app.py --help    - Show this help")

def interactive_mode(voice_assistant: VoiceAssistant):
    """Interactive mode dengan menu"""
    print("\n Interactive Mode")
    print("Choose your interaction style:")
    print("1. Single Voice (one-shot)")
    print("2. Text Chat (continuous)")
    print("3. Voice Chat (continuous)")
    print("4. Exit")
    
    while True:
        try:
            choice = input("\nSelect mode (1-4): ").strip()
            
            if choice == '1':
                voice_assistant.single_voice_interaction()
            elif choice == '2':
                voice_assistant.text_chat_mode()
            elif choice == '3':
                voice_assistant.voice_chat_mode()
            elif choice == '4':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please select 1-4.")
                
        except KeyboardInterrupt:
            print("\n Goodbye!")
            break

def main():
    """Main entry point"""
    try:
        show_banner()
        
        # Auto-start Ollama with configured model
        print("\n Starting Ollama service...")
        if not Config.start_ollama_model():
            print(" Ollama may not be ready, but continuing...")
        
        # Initialize dependency container
        container = DependencyContainer()
        voice_assistant = container.get_voice_assistant()
        
        # Parse command line arguments
        if len(sys.argv) > 1:
            mode = sys.argv[1].lower()
            
            if mode in ['--single', '-s']:
                voice_assistant.single_voice_interaction()
            elif mode in ['--text', '-t']:
                voice_assistant.text_chat_mode()
            elif mode in ['--voice', '-v']:
                voice_assistant.voice_chat_mode()
            elif mode in ['--check', '-c']:
                container.check_dependencies()
            elif mode in ['--help', '-h']:
                show_help()
            else:
                print(f"Unknown option: {mode}")
                show_help()
        else:
            # Interactive mode
            if container.check_dependencies():
                interactive_mode(voice_assistant)
            else:
                print("\n Run 'python app.py --check' to see what needs to be fixed")
                
    except KeyboardInterrupt:
        print("\n Program stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
