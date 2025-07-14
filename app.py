import logging
logging.basicConfig(level=logging.INFO)
#!/usr/bin/env python3
"""
Zorglub AI - Main Application Entry Point
Modern Architecture dengan Multiprocessing Support
"""

import sys
import os
from core.use_cases.voice_assistant import VoiceAssistant
from infrastructure import (
    quick_start, 
    print_system_status, 
    benchmark_performance,
    get_enhanced_ai_service,
    get_enhanced_stt_service, 
    get_enhanced_tts_service
)
from shared.config import Config

def show_banner():
    """Show welcome banner"""
    print("=" * 70)
    print("ZORGLUB AI - Advanced Voice Assistant")
    print("=" * 70)
    print("Modes:")
    print("  1. Single Voice - One recording, one response")
    print("  2. Text Chat    - Type your questions (with voice)")
    print("  3. Voice Chat   - Continuous voice conversation")
    print("  4. Text to Text - Text only (no voice output)")
    print("  5. System Check - Check system status")
    print("  6. Benchmark    - Performance comparison")
    print("=" * 70)
    print(f"AI Model: {Config.OLLAMA_MODEL}")
    print("Architecture: Modern Multiprocessing + Fallback Threading")
    print("=" * 70)
    logger = logging.getLogger("banner")
    logger.info("=" * 70)
    logger.info("ZORGLUB AI - Advanced Voice Assistant")
    logger.info("=" * 70)
    logger.info("Modes:")
    logger.info("  1. Single Voice - One recording, one response")
    logger.info("  2. Text Chat    - Type your questions (with voice)")
    logger.info("  3. Voice Chat   - Continuous voice conversation")
    logger.info("  4. Text to Text - Text only (no voice output)")
    logger.info("  5. System Check - Check system status")
    logger.info("  6. Benchmark    - Performance comparison")
    logger.info("=" * 70)
    logger.info(f"AI Model: {Config.OLLAMA_MODEL}")
    logger.info("Architecture: Modern Multiprocessing + Fallback Threading")
    logger.info("=" * 70)

def show_help():
    """Show available command line options"""
    print("\n USAGE:")
    print("  python app.py                - Interactive mode")
    print("  python app.py --single   -s  - Single voice interaction")
    print("  python app.py --text     -t  - Text chat mode (with voice)")
    print("  python app.py --voice    -v  - Voice chat mode")
    print("  python app.py --textonly -to - Text to text mode (no voice)")
    print("  python app.py --check    -c  - Check system status")
    print("  python app.py --status   -st - Show detailed system status")
    print("  python app.py --benchmark -b - Performance benchmark")
    print("  python app.py --threading -th- Force threading mode")
    print("  python app.py --help     -h  - Show this help")
    print("\n🔧 EXAMPLES:")
    print("  python app.py --voice --threading  # Voice mode with threading")
    print("  python app.py --benchmark          # Compare performance")
    print("  python app.py --check              # System health check")
    logger = logging.getLogger("help")
    logger.info("\n USAGE:")
    logger.info("  python app.py                - Interactive mode")
    logger.info("  python app.py --single   -s  - Single voice interaction")
    logger.info("  python app.py --text     -t  - Text chat mode (with voice)")
    logger.info("  python app.py --voice    -v  - Voice chat mode")
    logger.info("  python app.py --textonly -to - Text to text mode (no voice)")
    logger.info("  python app.py --check    -c  - Check system status")
    logger.info("  python app.py --status   -st - Show detailed system status")
    logger.info("  python app.py --benchmark -b - Performance benchmark")
    logger.info("  python app.py --threading -th- Force threading mode")
    logger.info("  python app.py --help     -h  - Show this help")
    logger.info("\n🔧 EXAMPLES:")
    logger.info("  python app.py --voice --threading  # Voice mode with threading")
    logger.info("  python app.py --benchmark          # Compare performance")
    logger.info("  python app.py --check              # System health check")

def interactive_mode(voice_assistant: VoiceAssistant):
    """Interactive mode dengan menu"""
    print("\n INTERACTIVE MODE")
    print("Choose your interaction style:")
    print("1. Single Voice (one-shot)")
    print("2. Text Chat (continuous with voice)")
    print("3. Voice Chat (continuous)")
    print("4. Text to Text (no voice output)")
    print("5. System Status")
    print("6. Exit")
    logger = logging.getLogger("interactive_mode")
    logger.info("\n INTERACTIVE MODE")
    logger.info("Choose your interaction style:")
    logger.info("1. Single Voice (one-shot)")
    logger.info("2. Text Chat (continuous with voice)")
    logger.info("3. Voice Chat (continuous)")
    logger.info("4. Text to Text (no voice output)")
    logger.info("5. System Status")
    logger.info("6. Exit")
    
    while True:
        try:
            choice = input("\n🔸 Select mode (1-6): ").strip()
            
            if choice == '1':
                voice_assistant.single_voice_interaction()
            elif choice == '2':
                voice_assistant.text_chat_mode()
            elif choice == '3':
                voice_assistant.voice_chat_mode()
            elif choice == '4':
                voice_assistant.text_to_text_mode()
            elif choice == '5':
                print_system_status(use_multiprocess=True)
            elif choice == '6':
                print("Goodbye!")
                break
            else:
                print("Invalid choice. Please select 1-6.")
                
        except KeyboardInterrupt:
            print("\n Goodbye!")
            break
            logger = logging.getLogger("interactive_mode")
            logger.info(f"User selected mode: {choice}")

def main():
    try:
        show_banner()
        
        # Parse command line arguments first
        args = parse_arguments()
        
        if args.get('help'):
            show_help()
            return
        
        # Auto-start Ollama
        print("\n Starting Ollama service...")
        if not Config.start_ollama_model():
            print("Ollama may not be ready, but continuing...")
        
        # Initialize services dengan pilihan mode
        use_multiprocess = args.get('multiprocess', True)
        if not quick_start(use_multiprocess=use_multiprocess):
            print("\n Failed to start services")
            return
        
        # Handle different modes
        handle_user_mode(args, use_multiprocess)
                
    except KeyboardInterrupt:
        print("\n rogram stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)
    logger = logging.getLogger("main")
    try:
        show_banner()
        # Parse command line arguments first
        args = parse_arguments()
        if args.get('help'):
            show_help()
            return
        # Auto-start Ollama
        logger.info("\n Starting Ollama service...")
        if not Config.start_ollama_model():
            logger.warning("Ollama may not be ready, but continuing...")
        # Initialize services dengan pilihan mode
        use_multiprocess = args.get('multiprocess', True)
        if not quick_start(use_multiprocess=use_multiprocess):
            logger.error("\n Failed to start services")
            return
        # Handle different modes
        handle_user_mode(args, use_multiprocess)
    except KeyboardInterrupt:
        logger.info("\n Program stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

def parse_arguments():
    args = {'multiprocess': True}  # Default to multiprocessing
    
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            arg_lower = arg.lower()
            if arg_lower in ['--single', '-s']:
                args['mode'] = 'single'
            elif arg_lower in ['--text', '-t']:
                args['mode'] = 'text'
            elif arg_lower in ['--voice', '-v']:
                args['mode'] = 'voice'
            elif arg_lower in ['--textonly', '-to']:
                args['mode'] = 'textonly'
            elif arg_lower in ['--check', '-c']:
                args['mode'] = 'check'
            elif arg_lower in ['--help', '-h']:
                args['help'] = True
            elif arg_lower in ['--threading', '-th']:
                args['multiprocess'] = False
            elif arg_lower in ['--benchmark', '-b']:
                args['mode'] = 'benchmark'
            elif arg_lower in ['--status', '-st']:
                args['mode'] = 'status'
    
    return args

def handle_user_mode(args, use_multiprocess):
    """Handle different user modes"""
    mode = args.get('mode')
    
    if mode == 'check':
        print_system_status(use_multiprocess)
    elif mode == 'benchmark':
        benchmark_performance()
    elif mode == 'status':
        print_system_status(use_multiprocess)
    elif mode in ['single', 'text', 'voice', 'textonly']:
        # Create voice assistant dengan enhanced services
        ai_service = get_enhanced_ai_service(use_multiprocess)
        stt_service = get_enhanced_stt_service(use_multiprocess)
        tts_service = get_enhanced_tts_service(use_multiprocess)
        
        voice_assistant = VoiceAssistant(ai_service, stt_service, tts_service)
        
        if mode == 'single':
            voice_assistant.single_voice_interaction()
        elif mode == 'text':
            voice_assistant.text_chat_mode()
        elif mode == 'voice':
            voice_assistant.voice_chat_mode()
        elif mode == 'textonly':
            voice_assistant.text_to_text_mode()
    else:
        # Interactive mode
        print_system_status(use_multiprocess)
        
        ai_service = get_enhanced_ai_service(use_multiprocess)
        stt_service = get_enhanced_stt_service(use_multiprocess)
        tts_service = get_enhanced_tts_service(use_multiprocess)
        
        voice_assistant = VoiceAssistant(ai_service, stt_service, tts_service)
        interactive_mode(voice_assistant)

if __name__ == "__main__":
    main()
