from abc import ABC, abstractmethod
from typing import Optional
from core.conversation_manager import ConversationManager

class AIServiceInterface(ABC):
    @abstractmethod
    def ask(self, prompt: str) -> str:
        pass
    
    @abstractmethod
    def ask_with_context(self, prompt: str, conversation_manager: ConversationManager) -> str:
        pass

class AIService(AIServiceInterface):
    def ask(self, prompt: str) -> str:
        from infrastructure.ollama_client import ask_gpt
        return ask_gpt(prompt)
    
    def ask_with_context(self, prompt: str, conversation_manager: ConversationManager) -> str:
        from infrastructure.ollama_client import ask_gpt_with_context
        
        # Get context-enhanced prompt
        context_prompt = conversation_manager.get_context_prompt(prompt)
        
        # Get AI response
        response = ask_gpt_with_context(context_prompt)
        
        # Add to conversation history
        context_tags = conversation_manager._detect_context(prompt)
        conversation_manager.add_message('user', prompt, context_tags)
        conversation_manager.add_message('assistant', response)
        
        return response
