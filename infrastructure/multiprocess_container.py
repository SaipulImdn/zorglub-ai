import multiprocessing as mp
import time
import signal
import os
from typing import Dict, Any, Optional, Callable
from contextlib import contextmanager

from .factories.multiprocess_base import (
    resource_manager, DependencyValidator, shared_memory_manager,
    ProcessPool, process_worker_initializer
)
from .factories.multiprocess_ai_factory import (
    get_multiprocess_ai_client, shutdown_ai_client, MultiprocessAIServiceFactory
)
from .factories.multiprocess_speech_factory import (
    get_multiprocess_stt_service, shutdown_stt_service, MultiprocessSpeechServiceFactory
)
from .factories.multiprocess_audio_factory import (
    get_multiprocess_tts_service, shutdown_tts_service, MultiprocessAudioServiceFactory
)

class MultiprocessServiceRegistry:
    def __init__(self):
        self._manager = mp.Manager()
        self._services = self._manager.dict()
        self._factories = self._manager.dict()
        self._lock = self._manager.Lock()
        self._health_status = self._manager.dict()
        self._process_pool: Optional[ProcessPool] = None
        
        self._register_builtin_factories()
    
    def _register_builtin_factories(self):
        factory_mappings = {
            'ai_service': 'multiprocess_ai_client',
            'stt_service': 'multiprocess_stt_service', 
            'tts_service': 'multiprocess_tts_service'
        }
        
        with self._lock:
            for service_name, factory_name in factory_mappings.items():
                self._factories[service_name] = factory_name
    
    def register_factory(self, service_name: str, factory_name: str):
        with self._lock:
            self._factories[service_name] = factory_name
    
    def get_service(self, service_name: str, **kwargs) -> Any:
        with self._lock:
            if service_name not in self._services:
                if service_name not in self._factories:
                    raise ValueError(f"Unknown service: {service_name}")
                
                factory_name = self._factories[service_name]
                service = self._create_service(factory_name, **kwargs)
                self._services[service_name] = service_name
                
                resource_manager.register_resource(service)
                
                return service
            else:
                return self._get_actual_service(service_name, **kwargs)
    
    def _create_service(self, factory_name: str, **kwargs) -> Any:
        if factory_name == 'multiprocess_ai_client':
            return get_multiprocess_ai_client(kwargs.get('max_workers'))
        elif factory_name == 'multiprocess_stt_service':
            return get_multiprocess_stt_service(kwargs.get('max_workers'))
        elif factory_name == 'multiprocess_tts_service':
            return get_multiprocess_tts_service(kwargs.get('max_workers'))
        else:
            raise ValueError(f"Unknown factory: {factory_name}")
    
    def _get_actual_service(self, service_name: str, **kwargs) -> Any:
        if service_name == 'ai_service':
            return get_multiprocess_ai_client(kwargs.get('max_workers'))
        elif service_name == 'stt_service':
            return get_multiprocess_stt_service(kwargs.get('max_workers'))
        elif service_name == 'tts_service':
            return get_multiprocess_tts_service(kwargs.get('max_workers'))
        else:
            raise ValueError(f"Unknown service: {service_name}")
    
    def health_check(self, service_name: str) -> bool:
        try:
            if service_name == 'ai_service':
                factory = MultiprocessAIServiceFactory()
                return factory.validate_dependencies()
            elif service_name == 'stt_service':
                factory = MultiprocessSpeechServiceFactory()
                return factory.validate_dependencies()
            elif service_name == 'tts_service':
                factory = MultiprocessAudioServiceFactory()
                return factory.validate_dependencies()
            else:
                return service_name in self._services
        except Exception:
            return False
    
    def get_all_health_status(self) -> Dict[str, bool]:
        status = {}
        for service_name in ['ai_service', 'stt_service', 'tts_service']:
            status[service_name] = self.health_check(service_name)
        return status
    
    def clear_services(self):
        with self._lock:
            shutdown_ai_client()
            shutdown_stt_service()
            shutdown_tts_service()
            
            self._services.clear()

class MultiprocessOptimizedContainer:
    def __init__(self, max_workers: Optional[int] = None):
        self.max_workers = max_workers or mp.cpu_count()
        self.registry = MultiprocessServiceRegistry()
        self._startup_tasks = []
        self._shutdown_tasks = []
        self._is_initialized = False
        self._manager = mp.Manager()
        self._lock = self._manager.Lock()
        self._worker_processes = self._manager.list()
        
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        def signal_handler(signum, frame):
            print(f"\nReceived signal {signum}, shutting down...")
            self.shutdown()
            exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def initialize(self, validate_parallel: bool = True) -> bool:
        with self._lock:
            if self._is_initialized:
                return True
            
            print("Initializing Zorglub AI services with multiprocessing...")
            
            if validate_parallel:
                validation_results = DependencyValidator.validate_all_parallel()
            else:
                validation_results = DependencyValidator.validate_all()
            
            missing_deps = [k for k, v in validation_results.items() if not v]
            
            if missing_deps:
                print(f"Missing dependencies: {missing_deps}")
                print("Some features may not work properly.")
                return False
            
            self._run_startup_tasks()
            
            shared_memory_manager.create_dict('system_stats', {
                'start_time': time.time(),
                'requests_processed': 0,
                'errors_encountered': 0
            })
            
            self._is_initialized = True
            print("All services initialized successfully with multiprocessing!")
            return True
    
    def _run_startup_tasks(self):
        if not self._startup_tasks:
            return
        
        with ProcessPool(
            max_workers=min(len(self._startup_tasks), self.max_workers),
            initializer=process_worker_initializer
        ) as pool:
            futures = [pool.submit(task) for task in self._startup_tasks]
            
            for future in futures:
                try:
                    future.result(timeout=30)
                except Exception as e:
                    print(f"Startup task failed: {e}")
    
    def shutdown(self):
        with self._lock:
            if not self._is_initialized:
                return
            
            print("Shutting down multiprocess services...")
            
            for task in self._shutdown_tasks:
                try:
                    task()
                except Exception as e:
                    print(f"Shutdown task failed: {e}")
            
            self.registry.clear_services()
            
            resource_manager.cleanup_all()
            shared_memory_manager.cleanup()
            
            self._terminate_worker_processes()
            
            self._is_initialized = False
            print("Services shutdown complete.")
    
    def _terminate_worker_processes(self):
        for process_info in self._worker_processes:
            try:
                pid = process_info.get('pid')
                if pid and pid != os.getpid():
                    os.kill(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError):
                pass
        
        self._worker_processes[:] = []
    
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

    def get_ai_service(self, max_workers: Optional[int] = None):
        return self.registry.get_service('ai_service', max_workers=max_workers)
    
    def get_speech_input(self, max_workers: Optional[int] = None):
        return self.registry.get_service('stt_service', max_workers=max_workers)
    
    def get_speech_output(self, max_workers: Optional[int] = None):
        return self.registry.get_service('tts_service', max_workers=max_workers)
    
    def get_voice_assistant(self):
        from core.use_cases.voice_assistant import VoiceAssistant
        from infrastructure.adapters import (
            AIServiceAdapter, SpeechToTextAdapter, TextToSpeechAdapter
        )
        
        ai_service = AIServiceAdapter()
        speech_input = SpeechToTextAdapter()
        speech_output = TextToSpeechAdapter()
        
        return VoiceAssistant(
            ai_service=ai_service,
            speech_input=speech_input,
            speech_output=speech_output
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        system_stats = shared_memory_manager.get_object('system_stats')
        
        health_data = {
            'initialized': self._is_initialized,
            'services': self.registry.get_all_health_status(),
            'timestamp': time.time(),
            'max_workers': self.max_workers,
            'active_processes': len(self._worker_processes),
            'cpu_count': mp.cpu_count()
        }
        
        if system_stats:
            uptime = time.time() - system_stats.get('start_time', time.time())
            health_data.update({
                'uptime_seconds': uptime,
                'requests_processed': system_stats.get('requests_processed', 0),
                'errors_encountered': system_stats.get('errors_encountered', 0)
            })
        
        return health_data
    
    def get_performance_stats(self) -> Dict[str, Any]:
        SERVICE_NOT_AVAILABLE = 'Service not available'
        stats = {}
        
        try:
            ai_client = get_multiprocess_ai_client()
            stats['ai_service'] = ai_client.get_stats()
        except Exception:
            stats['ai_service'] = {'error': SERVICE_NOT_AVAILABLE}
        
        try:
            stt_service = get_multiprocess_stt_service()
            stats['stt_service'] = stt_service.get_stats()
        except Exception:
            stats['stt_service'] = {'error': SERVICE_NOT_AVAILABLE}
        
        try:
            tts_service = get_multiprocess_tts_service()
            stats['tts_service'] = tts_service.get_stats()
        except Exception:
            stats['tts_service'] = {'error': SERVICE_NOT_AVAILABLE}
        
        return stats

_container: Optional[MultiprocessOptimizedContainer] = None

def get_multiprocess_container(max_workers: Optional[int] = None) -> MultiprocessOptimizedContainer:
    global _container
    
    if _container is None:
        _container = MultiprocessOptimizedContainer(max_workers=max_workers)
    
    return _container

def initialize_multiprocess_services(max_workers: Optional[int] = None, validate_parallel: bool = True) -> bool:
    container = get_multiprocess_container(max_workers)
    return container.initialize(validate_parallel=validate_parallel)

def shutdown_multiprocess_services():
    container = get_multiprocess_container()
    container.shutdown()

@contextmanager
def managed_multiprocess_services(max_workers: Optional[int] = None):
    container = get_multiprocess_container(max_workers)
    with container.managed_lifecycle():
        yield container
