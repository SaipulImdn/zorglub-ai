#!/usr/bin/env python3
"""
Test scripts for various TTS engines
Demo for a more human and natural voice
"""

import sys
import os
sys.path.append('/home/saipulimdn/project/backend/py/zorglub-ai')

from infrastructure.tts_human import HumanTTS

def test_human_tts():
    print("Testing Human-like TTS Engines")
    print("=" * 60)
    
    tts = HumanTTS()
    
    # Test text
    test_texts = [
        "Halo, saya adalah Zorglub AI dengan suara yang lebih natural",
        "Sekarang suara saya lebih human dan enak didengar",
        "Terima kasih telah menggunakan sistem voice assistant yang canggih"
    ]
    
    # List available engines
    print("\n Available TTS Engines:")
    engines = tts.list_available_engines()
    
    for engine_name, engine_info in engines.items():
        print(f"\n {engine_info['name']}:")
        print(f"   Quality: {engine_info['quality']}")
        print(f"   Human-like: {engine_info['human_like']}")
        print(f"   Languages: {', '.join(engine_info['languages'])}")
        print(f"   Requirement: {engine_info['requirement']}")
    
    # Test user choice
    print("\n" + "=" * 60)
    print("Test TTS Engines")
    
    while True:
        print("\nPilih engine untuk test:")
        print("1. Edge TTS (Most Human-like)")
        print("2. Piper TTS (Neural, Very Good)")
        print("3. Festival TTS (Classic)")
        print("4. Google TTS (Fallback)")
        print("5. Test All Engines")
        print("6. Exit")
        
        choice = input("\nSelect (1-6): ").strip()
        
        if choice == '1':
            engine = 'edge'
        elif choice == '2':
            engine = 'piper'
        elif choice == '3':
            engine = 'festival'
        elif choice == '4':
            engine = 'gtts'
        elif choice == '5':
            tts.test_engines()
            continue
        elif choice == '6':
            print("Goodbye!")
            break
        else:
            print("Invalid choice!")
            continue
        
        # Test selected engine
        print(f"\n Testing {engine} TTS...")
        
        for i, text in enumerate(test_texts, 1):
            print(f"\n Test {i}: {text}")
            success = tts.speak(text, engine)
            
            if success:
                print(f" {engine} TTS worked!")
            else:
                print(f" {engine} TTS failed!")
            
            if i < len(test_texts):
                input("Press Enter untuk next test...")
        
        print(f"\n {engine} TTS testing completed!")

if __name__ == "__main__":
    test_human_tts()
