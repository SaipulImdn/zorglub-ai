import logging
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class Message:
    role: str
    content: str
    timestamp: datetime
    context_tags: List[str] = None

    def __post_init__(self):
        if self.context_tags is None:
            self.context_tags = []

class ConversationManager:
    def __init__(self, max_history: int = 10):
        self.conversation_history: List[Message] = []
        self.max_history = max_history
        self.current_context = {}
        self.topics_discussed = set()
        
    def add_message(self, role: str, content: str, context_tags: List[str] = None):
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now(),
            context_tags=context_tags or []
        )
        
        self.conversation_history.append(message)
        
        if context_tags:
            self.topics_discussed.update(context_tags)
        if len(self.conversation_history) > self.max_history:
            self.conversation_history = self.conversation_history[-self.max_history:]
    
    def get_context_prompt(self, new_user_input: str) -> str:
        context_tags = self._detect_context(new_user_input)
        context_messages = []
        
        for msg in self.conversation_history[-5:]:
            context_messages.append(f"{msg.role.title()}: {msg.content}")
        
        is_followup = self._is_followup_question(new_user_input)
        
        prompt_parts = []
        
        if context_messages:
            prompt_parts.append("=== CONVERSATION HISTORY ===")
            prompt_parts.extend(context_messages)
            prompt_parts.append("=== END HISTORY ===\n")
        
        if is_followup:
            prompt_parts.append("INSTRUCTION: Ini adalah pertanyaan lanjutan. Jawab berdasarkan context percakapan sebelumnya.")
        
        if self.topics_discussed:
            topics = ", ".join(list(self.topics_discussed)[:3])
            prompt_parts.append(f"TOPICS DISCUSSED: {topics}")
        
        prompt_parts.append(f"USER: {new_user_input}")
        
        prompt_parts.append("\nINSTRUCTION: Berikan jawaban yang natural dan mengacu pada percakapan sebelumnya jika relevan. Gunakan bahasa Indonesia yang casual dan friendly.")
        
        return "\n".join(prompt_parts)
    
    def _detect_context(self, text: str) -> List[str]:
        text_lower = text.lower()
        
        context_map = {
            'programming': ['code', 'programming', 'python', 'javascript', 'coding', 'bug', 'error'],
            'general': ['halo', 'hai', 'hello', 'hi', 'apa kabar', 'gimana'],
            'question': ['apa', 'bagaimana', 'mengapa', 'kenapa', 'siapa', 'kapan', 'dimana'],
            'follow_up': ['itu', 'tadi', 'sebelumnya', 'lanjutannya', 'terus', 'lalu'],
            'technical': ['cara', 'tutorial', 'belajar', 'install', 'setup', 'konfigurasi'],
            'personal': ['saya', 'aku', 'kamu', 'kita', 'cerita', 'sharing']
        }
        
        detected_tags = []
        for tag, keywords in context_map.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_tags.append(tag)
        
        return detected_tags
    
    def _is_followup_question(self, text: str) -> bool:
        followup_indicators = [
            'itu', 'tadi', 'sebelumnya', 'yang', 'lanjutannya', 
            'terus', 'lalu', 'kemudian', 'selanjutnya', 'bagaimana dengan',
            'dan', 'tapi', 'namun', 'kalau', 'kalo'
        ]
        
        text_lower = text.lower()
        has_followup = any(indicator in text_lower for indicator in followup_indicators)
        has_recent_history = len(self.conversation_history) > 0
        
        return has_followup and has_recent_history
    
    def get_conversation_summary(self) -> Dict:
        return {
            'total_messages': len(self.conversation_history),
            'topics_discussed': list(self.topics_discussed),
            'last_message_time': self.conversation_history[-1].timestamp.isoformat() if self.conversation_history else None,
            'recent_messages': [
                {'role': msg.role, 'content': msg.content[:50] + '...' if len(msg.content) > 50 else msg.content}
                for msg in self.conversation_history[-3:]
            ]
        }
    
    def clear_conversation(self):
        self.conversation_history.clear()
        self.topics_discussed.clear()
        self.current_context.clear()
        logging.getLogger(__name__).info("Conversation history cleared")
    
    def save_conversation(self, filename: str = None):
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"conversation_{timestamp}.json"
        data = {
            'conversation_history': [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'context_tags': msg.context_tags
                }
                for msg in self.conversation_history
            ],
            'topics_discussed': list(self.topics_discussed)
        }
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logging.getLogger(__name__).info(f"Conversation saved to {filename}")
    
    def load_conversation(self, filename: str):
        logger = logging.getLogger(__name__)
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.conversation_history = [
                Message(
                    role=msg.role,
                    content=msg.content,
                    timestamp=datetime.fromisoformat(msg.timestamp),
                    context_tags=msg.context_tags or []
                )
                for msg in data['conversation_history']
            ]
            self.topics_discussed = set(data.get('topics_discussed', []))
            logger.info(f"Conversation loaded from {filename}")
        except Exception as e:
            logger.error(f"Error loading conversation: {e}")
    
    def get_conversation_history(self) -> List[Message]:
        return self.conversation_history.copy()
    
    def get_recent_history(self, count: int = 5) -> List[Message]:
        return self.conversation_history[-count:] if count > 0 else []
