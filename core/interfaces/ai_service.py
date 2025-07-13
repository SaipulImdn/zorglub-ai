from abc import ABC, abstractmethod

class AIServiceInterface(ABC):
    @abstractmethod
    def ask(self, prompt: str) -> str:
        pass

class AIService(AIServiceInterface):
    def ask(self, prompt: str) -> str:
        from infrastructure.ollama_client import ask_gpt
        return ask_gpt(prompt)
