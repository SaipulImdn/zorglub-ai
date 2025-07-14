from abc import ABC, abstractmethod
from typing import Type, TypeVar, Generic, Dict, Any, Optional
import asyncio
import threading
from contextlib import contextmanager

T = TypeVar('T')

class ServiceFactory(ABC, Generic[T]):
    @abstractmethod
    def create(self, **kwargs) -> T:
        pass
    
    @abstractmethod
    def validate_dependencies(self) -> bool:
        pass

class SingletonMixin:
    _instances: Dict[Type, Any] = {}
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

class ResourceManager:
    def __init__(self):
        self._resources = []
        self._cleanup_callbacks = []
    
    def register_resource(self, resource: Any, cleanup_func: Optional[callable] = None):
        self._resources.append(resource)
        if cleanup_func:
            self._cleanup_callbacks.append(cleanup_func)
    
    def cleanup_all(self):
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error during cleanup: {e}")
        
        self._resources.clear()
        self._cleanup_callbacks.clear()
    
    @contextmanager
    def managed_resource(self, resource: Any, cleanup_func: Optional[callable] = None):
        self.register_resource(resource, cleanup_func)
        try:
            yield resource
        finally:
            if cleanup_func:
                try:
                    cleanup_func()
                except Exception as e:
                    print(f"Error during cleanup: {e}")

class DependencyValidator:
    @staticmethod
    def validate_all() -> Dict[str, bool]:
        from .ai_factory import AIServiceFactory
        from .speech_factory import SpeechServiceFactory
        from .audio_factory import AudioServiceFactory
        
        results = {}
        
        ai_factory = AIServiceFactory()
        results['ai_service'] = ai_factory.validate_dependencies()
        
        speech_factory = SpeechServiceFactory()
        results['speech_service'] = speech_factory.validate_dependencies()
        
        audio_factory = AudioServiceFactory()
        results['audio_service'] = audio_factory.validate_dependencies()
        
        return results
    
    @staticmethod
    def get_missing_dependencies() -> list:
        results = DependencyValidator.validate_all()
        return [key for key, value in results.items() if not value]

resource_manager = ResourceManager()
