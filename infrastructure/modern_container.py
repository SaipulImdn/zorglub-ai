import asyncio
import threading
import time
from typing import Dict, Any, Optional, TypeVar, Type, Callable
from contextlib import contextmanager

from .factories.base_factory import resource_manager, DependencyValidator
from .factories.ai_factory import get_ai_client, AIServiceFactory
from .factories.speech_factory import get_stt_service, SpeechServiceFactory
from .factories.audio_factory import get_tts_service, AudioServiceFactory

T = TypeVar('T')

class ServiceRegistry:
    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._lock = threading.RLock()
        self._health_status: Dict[str, bool] = {}
        
        # Register built-in factories
        self._register_builtin_factories()
    
    def _register_builtin_factories(self):
        self._factories.update({
            'ai_service': get_ai_client,
            'stt_service': get_stt_service,
            'tts_service': get_tts_service
        })
    
    def register_factory(self, service_name: str, factory: Callable):
        with self._lock:
            self._factories[service_name] = factory
    
    def get_service(self, service_name: str, **kwargs) -> Any:
        with self._lock:
            if service_name not in self._services:
                if service_name not in self._factories:
                    raise ValueError(f"Unknown service: {service_name}")
                
                factory = self._factories[service_name]
                self._services[service_name] = factory(**kwargs)
                
                # Register for cleanup
                resource_manager.register_resource(self._services[service_name])
            
            return self._services[service_name]
    
    def health_check(self, service_name: str) -> bool:
        try:
            if service_name == 'ai_service':
                factory = AIServiceFactory()
                return factory.validate_dependencies()
            elif service_name == 'stt_service':
                factory = SpeechServiceFactory()
                return factory.validate_dependencies()
            elif service_name == 'tts_service':
                factory = AudioServiceFactory()
                return factory.validate_dependencies()
            else:
                return service_name in self._services
        except Exception:
            return False
    
    def get_all_health_status(self) -> Dict[str, bool]:
        status = {}
        for service_name in self._factories.keys():
            status[service_name] = self.health_check(service_name)
        return status
    
    def clear_services(self):
        with self._lock:
            self._services.clear()

class OptimizedContainer:
    def __init__(self):
        self.registry = ServiceRegistry()
        self._startup_tasks = []
        self._shutdown_tasks = []
        self._is_initialized = False
        self._lock = threading.Lock()
    
    def initialize(self) -> bool:
        with self._lock:
            if self._is_initialized:
                return True
            
            print("Initializing Zorglub AI services...")
            
            # Validate dependencies
            validation_results = DependencyValidator.validate_all()
            missing_deps = [k for k, v in validation_results.items() if not v]
            
            if missing_deps:
                print(f"Missing dependencies: {missing_deps}")
                print("Some features may not work properly.")
                return False
            
            # Run startup tasks
            for task in self._startup_tasks:
                try:
                    task()
                except Exception as e:
                    print(f"Startup task failed: {e}")
            
            self._is_initialized = True
            print("All services initialized successfully!")
            return True
    
    def shutdown(self):
        """Shutdown container dan cleanup resources"""
        with self._lock:
            if not self._is_initialized:
                return
            
            print("Shutting down services...")
            
            # Run shutdown tasks
            for task in self._shutdown_tasks:
                try:
                    task()
                except Exception as e:
                    print(f"Shutdown task failed: {e}")
            
            # Cleanup resources
            resource_manager.cleanup_all()
            self.registry.clear_services()
            
            self._is_initialized = False
            print("Services shutdown complete.")
    
    def add_startup_task(self, task: Callable):
        self._startup_tasks.append(task)
    
    def add_shutdown_task(self, task: Callable):
        self._shutdown_tasks.append(task)
    
    @contextmanager
    def managed_lifecycle(self):
        try:
            success = self.initialize()
            if not success:
                print("Initialization failed, continuing with limited functionality")
            yield self
        finally:
            self.shutdown()
    
    # Service accessors
    def get_ai_service(self):
        """Get AI service instance"""
        return self.registry.get_service('ai_service')
    
    def get_speech_input(self):
        """Get speech input service"""
        return self.registry.get_service('stt_service')
    
    def get_speech_output(self):
        """Get speech output service"""
        return self.registry.get_service('tts_service')
    
    def get_voice_assistant(self):
        """Get voice assistant dengan auto-wiring"""
        from core.use_cases.voice_assistant import VoiceAssistant
        from core.interfaces.ai_service import AIService
        from core.interfaces.speech_input import SpeechToText
        from core.interfaces.speech_output import TextToSpeech
        
        # Create adapter instances
        ai_service = AIService()
        speech_input = SpeechToText()
        speech_output = TextToSpeech()
        
        return VoiceAssistant(
            ai_service=ai_service,
            speech_input=speech_input,
            speech_output=speech_output
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        return {
            'initialized': self._is_initialized,
            'services': self.registry.get_all_health_status(),
            'timestamp': time.time()
        }

# Global container instance
_container: Optional[OptimizedContainer] = None

def get_container() -> OptimizedContainer:
    """Get global container instance"""
    global _container
    
    if _container is None:
        _container = OptimizedContainer()
    
    return _container

def initialize_services() -> bool:
    """Initialize all services"""
    container = get_container()
    return container.initialize()

def shutdown_services():
    """Shutdown all services"""
    container = get_container()
    container.shutdown()

@contextmanager
def managed_services():
    """Context manager for service lifecycle"""
    container = get_container()
    with container.managed_lifecycle():
        yield container
