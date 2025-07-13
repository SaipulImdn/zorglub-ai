#!/usr/bin/env python3
"""
Test script untuk conversation logic
"""

from core.conversation_manager import ConversationManager

def test_conversation_logic():
    print("Testing Conversation Logic...")
    print("=" * 50)
    
    # Create conversation manager
    cm = ConversationManager()
    
    # Test 1: Basic conversation
    print("Test 1: Basic conversation")
    user1 = "Halo, nama saya John"
    context_prompt1 = cm.get_context_prompt(user1)
    print(f"User: {user1}")
    print(f"Context Enhanced: {context_prompt1}")
    
    # Simulate AI response
    ai1 = "Halo John! Senang berkenalan dengan Anda."
    cm.add_message('user', user1)
    cm.add_message('assistant', ai1)
    
    print("\n Test 2: Follow-up question")
    user2 = "Apa yang bisa kamu lakukan?"
    context_prompt2 = cm.get_context_prompt(user2)
    print(f"User: {user2}")
    print(f"Context Enhanced: {context_prompt2}")
    
    ai2 = "Saya bisa membantu Anda dengan berbagai hal, John!"
    cm.add_message('user', user2)
    cm.add_message('assistant', ai2)
    
    print("\n Test 3: Follow-up with context reference")
    user3 = "Itu bagus! Bisa kasih contoh yang lebih spesifik?"
    context_prompt3 = cm.get_context_prompt(user3)
    print(f"User: {user3}")
    print(f"Context Enhanced: {context_prompt3}")
    
    print("\n Conversation Summary:")
    summary = cm.get_conversation_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\n Conversation logic test completed!")

if __name__ == "__main__":
    test_conversation_logic()
