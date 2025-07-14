from abc import ABC, abstractmethod
from typing import Type, TypeVar, Generic, Dict, Any, Optional
import asyncio
import threading
from contextlib import contextmanager

T = TypeVar('T')

class ServiceFactory(ABC, Generic[T]):
    """Abstract factory untuk service creation"""
    
    @abstractmethod
    def create(self, **kwargs) -> T:
        """Create service instance"""
        pass
    
    @abstractmethod
    def validate_dependencies(self) -> bool:
        """Validate required dependencies"""
        pass

class SingletonMixin:
    """Mixin untuk singleton pattern yang thread-safe"""
    
    _instances: Dict[Type, Any] = {}
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

class ResourceManager:
    """Resource management untuk cleanup dan lifecycle"""
    
    def __init__(self):
        self._resources = []
        self._cleanup_callbacks = []
    
    def register_resource(self, resource: Any, cleanup_func: Optional[callable] = None):
        """Register resource untuk automatic cleanup"""
        self._resources.append(resource)
        if cleanup_func:
            self._cleanup_callbacks.append(cleanup_func)
    
    def cleanup_all(self):
        """Cleanup semua registered resources"""
        for callback in self._cleanup_callbacks:
            try:
                callback()
            except Exception as e:
                print(f"Error during cleanup: {e}")
        
        self._resources.clear()
        self._cleanup_callbacks.clear()
    
    @contextmanager
    def managed_resource(self, resource: Any, cleanup_func: Optional[callable] = None):
        """Context manager untuk resource management"""
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
    """Validator untuk system dependencies"""
    
    @staticmethod
    def validate_all() -> Dict[str, bool]:
        """Validate semua dependencies dan return status"""
        from .ai_factory import AIServiceFactory
        from .speech_factory import SpeechServiceFactory
        from .audio_factory import AudioServiceFactory
        
        results = {}
        
        # Validate AI service
        ai_factory = AIServiceFactory()
        results['ai_service'] = ai_factory.validate_dependencies()
        
        # Validate speech services
        speech_factory = SpeechServiceFactory()
        results['speech_service'] = speech_factory.validate_dependencies()
        
        # Validate audio services
        audio_factory = AudioServiceFactory()
        results['audio_service'] = audio_factory.validate_dependencies()
        
        return results
    
    @staticmethod
    def get_missing_dependencies() -> list:
        """Get list of missing dependencies"""
        results = DependencyValidator.validate_all()
        return [key for key, value in results.items() if not value]

# Global resource manager instance
resource_manager = ResourceManager()
