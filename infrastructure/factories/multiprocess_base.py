from abc import ABC, abstractmethod
from typing import Type, TypeVar, Generic, Dict, Any, Optional
import multiprocessing as mp
import multiprocessing.managers
import asyncio
import signal
import os
from contextlib import contextmanager
from concurrent.futures import ProcessPoolExecutor, as_completed
import pickle
import queue

T = TypeVar('T')

class ServiceFactory(ABC, Generic[T]):
    @abstractmethod
    def create(self, **kwargs) -> T:
        """Create service instance"""
        pass
    
    @abstractmethod
    def validate_dependencies(self) -> bool:
        """Validate required dependencies"""
        pass

class MultiprocessSingletonMixin:
    _instances: Dict[Type, Any] = {}
    _manager = mp.Manager()
    _lock = _manager.Lock()
    
    def __new__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super().__new__(cls)
        return cls._instances[cls]

class ProcessSafeQueue:
    def __init__(self, maxsize: int = 0):
        self._queue = mp.Queue(maxsize)
        self._manager = mp.Manager()
        self._stats = self._manager.dict({
            'total_items': 0,
            'processed_items': 0,
            'errors': 0
        })
    
    def put(self, item: Any, timeout: Optional[float] = None):
        try:
            self._queue.put(item, timeout=timeout)
            self._stats['total_items'] += 1
        except queue.Full as e:
            raise queue.Full(f"Queue is full, cannot add item: {item}") from e
    
    def get(self, timeout: Optional[float] = None) -> Any:
        try:
            item = self._queue.get(timeout=timeout)
            self._stats['processed_items'] += 1
            return item
        except queue.Empty as e:
            raise queue.Empty("No items available in queue") from e
    
    def empty(self) -> bool:
        return self._queue.empty()
    
    def qsize(self) -> int:
        return self._queue.qsize()
    
    def get_stats(self) -> Dict[str, int]:
        return dict(self._stats)

class ProcessPool:
    def __init__(self, max_workers: Optional[int] = None, initializer=None, initargs=()):
        self.max_workers = max_workers or mp.cpu_count()
        self.initializer = initializer
        self.initargs = initargs
        self._executor: Optional[ProcessPoolExecutor] = None
        self._active_futures = []
        
    def __enter__(self):
        self._executor = ProcessPoolExecutor(
            max_workers=self.max_workers,
            initializer=self.initializer,
            initargs=self.initargs
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._executor:
            # Cancel active futures
            for future in self._active_futures:
                future.cancel()
            
            # Shutdown executor
            self._executor.shutdown(wait=True)
            self._executor = None
            self._active_futures.clear()
    
    def submit(self, fn, *args, **kwargs):
        if not self._executor:
            raise RuntimeError("ProcessPool not initialized. Use with context manager.")
        
        future = self._executor.submit(fn, *args, **kwargs)
        self._active_futures.append(future)
        return future
    
    def map(self, fn, iterable, timeout=None, chunksize=1):
        if not self._executor:
            raise RuntimeError("ProcessPool not initialized. Use with context manager.")
        
        return self._executor.map(fn, iterable, timeout=timeout, chunksize=chunksize)
    
    def as_completed(self, timeout=None):
        return as_completed(self._active_futures, timeout=timeout)

class SharedMemoryManager:
    def __init__(self):
        self._manager = mp.Manager()
        self._shared_objects = {}
    
    def create_dict(self, name: str, initial_data: Optional[Dict] = None) -> Dict:
        shared_dict = self._manager.dict(initial_data or {})
        self._shared_objects[name] = shared_dict
        return shared_dict
    
    def create_list(self, name: str, initial_data: Optional[list] = None) -> list:
        shared_list = self._manager.list(initial_data or [])
        self._shared_objects[name] = shared_list
        return shared_list
    
    def get_object(self, name: str):
        return self._shared_objects.get(name)
    
    def cleanup(self):
        self._shared_objects.clear()
        if hasattr(self._manager, 'shutdown'):
            self._manager.shutdown()

class ProcessSafeResourceManager:
    def __init__(self):
        self._manager = mp.Manager()
        self._resources = self._manager.list()
        self._cleanup_callbacks = self._manager.list()
        self._process_registry = self._manager.dict()
        
    def register_resource(self, resource: Any, cleanup_func: Optional[callable] = None):
        # Store resource info instead of object directly (for pickling)
        resource_info = {
            'type': type(resource).__name__,
            'id': id(resource),
            'pid': os.getpid()
        }
        self._resources.append(resource_info)
        
        if cleanup_func:
            # Store cleanup function info
            cleanup_info = {
                'func_name': cleanup_func.__name__ if hasattr(cleanup_func, '__name__') else str(cleanup_func),
                'resource_id': id(resource)
            }
            self._cleanup_callbacks.append(cleanup_info)
    
    def register_process(self, process_name: str, process: mp.Process):
        self._process_registry[process_name] = {
            'pid': process.pid,
            'is_alive': process.is_alive(),
            'exitcode': process.exitcode
        }
    
    def cleanup_all(self):
        current_pid = os.getpid()
        
        # Cleanup resources dari current process
        for callback_info in self._cleanup_callbacks:
            try:
                # Execute cleanup - in real implementation, you'd need to 
                # maintain actual function references per process
                print(f"Cleaning up resource: {callback_info}")
            except Exception as e:
                print(f"Error during cleanup: {e}")
        
        # Terminate registered processes
        for process_name, process_info in self._process_registry.items():
            if process_info['is_alive']:
                try:
                    # Send terminate signal
                    if process_info['pid'] != current_pid:
                        os.kill(process_info['pid'], signal.SIGTERM)
                except (ProcessLookupError, PermissionError):
                    pass
        
        self._resources[:] = []
        self._cleanup_callbacks[:] = []
        self._process_registry.clear()
    
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

def process_worker_initializer():
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    signal.signal(signal.SIGTERM, signal.default_int_handler)
    
    # Set process title
    try:
        import setproctitle
        setproctitle.setproctitle("zorglub-worker")
    except ImportError:
        pass

class DependencyValidator:
    @staticmethod
    def validate_dependency(dependency_name: str) -> bool:
        try:
            if dependency_name == 'ai_service':
                from .ai_factory import AIServiceFactory
                factory = AIServiceFactory()
                return factory.validate_dependencies()
            elif dependency_name == 'speech_service':
                from .speech_factory import SpeechServiceFactory
                factory = SpeechServiceFactory()
                return factory.validate_dependencies()
            elif dependency_name == 'audio_service':
                from .audio_factory import AudioServiceFactory
                factory = AudioServiceFactory()
                return factory.validate_dependencies()
            else:
                return False
        except Exception:
            return False
    
    @staticmethod
    def validate_all_parallel() -> Dict[str, bool]:
        dependencies = ['ai_service', 'speech_service', 'audio_service']
        
        with ProcessPool(max_workers=3, initializer=process_worker_initializer) as pool:
            # Submit validation tasks
            futures = {
                dep: pool.submit(DependencyValidator.validate_dependency, dep)
                for dep in dependencies
            }
            
            # Collect results
            results = {}
            for dep, future in futures.items():
                try:
                    results[dep] = future.result(timeout=30)
                except Exception as e:
                    print(f"Validation failed for {dep}: {e}")
                    results[dep] = False
            
            return results
    
    @staticmethod
    def validate_all() -> Dict[str, bool]:
        try:
            return DependencyValidator.validate_all_parallel()
        except Exception as e:
            print(f"Parallel validation failed, falling back to sequential: {e}")
            
            # Fallback to sequential validation
            results = {}
            dependencies = ['ai_service', 'speech_service', 'audio_service']
            
            for dep in dependencies:
                results[dep] = DependencyValidator.validate_dependency(dep)
            
            return results
    
    @staticmethod
    def get_missing_dependencies() -> list:
        results = DependencyValidator.validate_all()
        return [key for key, value in results.items() if not value]

# Global instances
shared_memory_manager = SharedMemoryManager()
resource_manager = ProcessSafeResourceManager()

# Process pool configuration
DEFAULT_POOL_CONFIG = {
    'max_workers': mp.cpu_count(),
    'initializer': process_worker_initializer,
    'initargs': ()
}
