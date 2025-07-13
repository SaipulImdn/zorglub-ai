"""
Voice Assistant Use Case
Orchestrates voice interactions with conversation context
"""

from core.interfaces.ai_service import AIService
from core.interfaces.speech_input import SpeechToText
from core.interfaces.speech_output import TextToSpeech
from core.conversation_manager import ConversationManager

class VoiceAssistant:
    def __init__(self, ai_service: AIService, speech_input: SpeechToText, speech_output: TextToSpeech):
        self.ai_service = ai_service
        self.speech_input = speech_input
        self.speech_output = speech_output
        self.conversation_manager = ConversationManager(max_history=15)  # Keep longer history

    def single_voice_interaction(self):
        """Single voice recording and response"""
        print("\n Single Voice Interaction")
        print("-" * 30)
        
        # Get voice input
        user_input = self.speech_input.listen()
        if not user_input:
            print("Tidak ada input yang terdeteksi")
            return
        
        print(f"👤 Anda: {user_input}")
        
        # Get AI response dengan conversation context
        ai_response = self.ai_service.ask_with_context(user_input, self.conversation_manager)
        print(f"AI: {ai_response}")
        
        # Speak response
        self.speech_output.speak(ai_response)

    def text_chat_mode(self):
        """Text input chat mode dengan conversation context"""
        print("\n Text Chat Mode")
        print("-" * 20)
        print("Type your questions (or /quit to exit)")
        print("AI akan mengingat percakapan sebelumnya untuk respon yang lebih natural")
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['/quit', '/exit', 'quit', 'exit']:
                    break
                elif user_input.lower() == '/help':
                    self._show_help()
                    continue
                elif user_input.lower() == '/clear':
                    self.conversation_manager.clear_conversation()
                    continue
                elif user_input.lower() == '/status':
                    self._show_conversation_status()
                    continue
                elif not user_input:
                    continue
                
                # Get AI response dengan conversation context
                ai_response = self.ai_service.ask_with_context(user_input, self.conversation_manager)
                print(f"🤖 AI: {ai_response}")
                
                # Speak response
                self.speech_output.speak(ai_response)
                
            except KeyboardInterrupt:
                print("\n Exiting text chat...")
                break

    def voice_chat_mode(self):
        """Continuous voice chat mode dengan conversation context"""
        print("\n Voice Chat Mode")
        print("-" * 20)
        print("Say 'quit' or 'berhenti' to exit, or press Ctrl+C")
        print("AI akan mengingat percakapan untuk respon yang lebih natural")
        
        while True:
            try:
                print("\n" + "="*40)
                user_input = self.speech_input.listen()
                
                if not user_input:
                    print("Tidak ada input. Coba lagi...")
                    continue
                
                print(f"Anda: {user_input}")
                
                # Check exit commands
                if any(word in user_input.lower() for word in ['quit', 'exit', 'stop', 'berhenti']):
                    print("Stopping voice chat...")
                    break
                
                # Get AI response dengan conversation context
                ai_response = self.ai_service.ask_with_context(user_input, self.conversation_manager)
                print(f"AI: {ai_response}")
                
                # Speak response
                self.speech_output.speak(ai_response)
                
            except KeyboardInterrupt:
                print("\n Exiting voice chat...")
                break

    def _show_help(self):
        """Show help commands"""
        print("\n Commands:")
        print("  /help   - Show this help")
        print("  /quit   - Exit current mode")
        print("  /clear  - Clear conversation history")
        print("  /status - Show conversation status")
        print("  Type any question to get AI response with voice")
        print("\n AI Features:")
        print("  Remembers conversation context")
        print("  Detects follow-up questions")
        print("  Natural conversation flow")
    
    def _show_conversation_status(self):
        """Show current conversation status"""
        summary = self.conversation_manager.get_conversation_summary()
        print(f"\n Conversation Status:")
        print(f"  Messages: {summary['total_messages']}")
        print(f"  Topics: {', '.join(summary['topics_discussed']) if summary['topics_discussed'] else 'None'}")
        
        if summary['recent_messages']:
            print(f"  Recent messages:")
            for msg in summary['recent_messages']:
                print(f"    {msg['role']}: {msg['content']}")
    
    def save_conversation(self, filename: str = None):
        """Save current conversation"""
        self.conversation_manager.save_conversation(filename)
    
    def load_conversation(self, filename: str):
        """Load previous conversation"""
        self.conversation_manager.load_conversation(filename)
