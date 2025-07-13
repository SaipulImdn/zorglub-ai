#!/usr/bin/env python3
"""
Demo conversation dengan context untuk menunjukkan
conversation logic yang lebih natural seperti n8n workflow
"""

import os
import sys
sys.path.append('/home/saipulimdn/project/backend/py/zorglub-ai')

from core.conversation_manager import ConversationManager
from infrastructure.ollama_client import ask_gpt_with_context

def demo_conversation():
    print("🎭 DEMO: Natural Conversation Logic")
    print("=" * 60)
    print("Simulasi percakapan dengan AI yang mengingat context")
    print("seperti workflow n8n yang saling terhubung")
    print("=" * 60)
    
    cm = ConversationManager()
    
    # Conversation flow demo
    conversations = [
        "Halo, nama saya Saipul",
        "Saya sedang belajar Python",
        "Apa yang bisa saya buat dengan Python?",
        "Yang tadi itu bagus! Bisa kasih contoh project sederhana?",
        "Kalau untuk project voice assistant seperti ini gimana?"
    ]
    
    for i, user_input in enumerate(conversations, 1):
        print(f"\n Step {i}:")
        print(f"User: {user_input}")
        
        # Get context-enhanced prompt
        context_prompt = cm.get_context_prompt(user_input)
        
        print("Context Enhanced Prompt:")
        print("-" * 40)
        print(context_prompt)
        print("-" * 40)
        
        # Simulate AI response (tanpa call ke ollama untuk demo)
        if i == 1:
            ai_response = "Halo Saipul! Senang berkenalan dengan Anda. Ada yang bisa saya bantu hari ini?"
        elif i == 2:
            ai_response = "Wah bagus Saipul! Python itu bahasa yang sangat versatile. Anda belajar untuk tujuan apa?"
        elif i == 3:
            ai_response = "Dengan Python, Saipul bisa buat banyak hal! Web development dengan Django/Flask, data science dengan pandas, automation scripts, AI/ML dengan TensorFlow, dan masih banyak lagi."
        elif i == 4:
            ai_response = "Tentu Saipul! Untuk pemula, coba buat calculator sederhana, to-do list app, atau web scraper untuk ambil data dari website. Mau yang mana?"
        else:
            ai_response = "Voice assistant seperti yang kita gunakan sekarang adalah project yang bagus, Saipul! Ini menggabungkan speech recognition, AI, dan text-to-speech. Anda sudah punya foundationnya!"
        
        print(f"AI: {ai_response}")
        
        # Add to conversation history
        context_tags = cm._detect_context(user_input)
        cm.add_message('user', user_input, context_tags)
        cm.add_message('assistant', ai_response)
        
        print(f"Detected tags: {context_tags}")
        
        input("\nPress Enter untuk lanjut...")
    
    print("\n Final Conversation Summary:")
    summary = cm.get_conversation_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n  Conversation Features Demonstrated:")
    print("    Context awareness - AI tahu nama user")
    print("    Topic continuity - mengingat topik Python")
    print("    Follow-up detection - 'Yang tadi itu', 'Kalau untuk'")
    print("    Reference resolution - AI tahu konteks 'seperti ini'")
    print("    Natural flow - percakapan mengalir seperti manusia")

if __name__ == "__main__":
    demo_conversation()
