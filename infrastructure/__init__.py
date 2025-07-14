# Import modern components
from .modern_container import (
    get_container,
    initialize_services,
    shutdown_services,
    managed_services
)

# Import multiprocess components
from .multiprocess_container import (
    get_multiprocess_container,
    initialize_multiprocess_services,
    shutdown_multiprocess_services,
    managed_multiprocess_services
)

from .enhanced_config import (
    get_config,
    EnhancedConfig,
    OllamaConfig,
    SpeechConfig,
    AudioConfig,
    PerformanceConfig
)

# Regular factories
from .factories.ai_factory import get_ai_client
from .factories.speech_factory import get_stt_service
from .factories.audio_factory import get_tts_service

# Multiprocess factories
from .factories.multiprocess_ai_factory import get_multiprocess_ai_client
from .factories.multiprocess_speech_factory import get_multiprocess_stt_service
from .factories.multiprocess_audio_factory import get_multiprocess_tts_service

from .factories.base_factory import resource_manager, DependencyValidator

# Import adapters untuk backward compatibility
from .adapters import (
    AIServiceAdapter,
    SpeechToTextAdapter,
    TextToSpeechAdapter,
    get_enhanced_ai_service,
    get_enhanced_stt_service,
    get_enhanced_tts_service
)


# Centralized logging setup
import logging
def setup_logging(level=logging.INFO, log_format=None):
    if log_format is None:
        log_format = "[%(asctime)s] %(levelname)s %(name)s: %(message)s"
    logging.basicConfig(level=level, format=log_format)
    logging.getLogger("multiprocessing").setLevel(logging.WARNING)

setup_logging()

import time
import threading
import multiprocessing as mp
from typing import Dict, Any, Optional

class PerformanceMonitor:
    def __init__(self, use_multiprocess: bool = True):
        self.use_multiprocess = use_multiprocess
        
        if use_multiprocess:
            self._manager = mp.Manager()
            self._metrics = self._manager.dict({
                'requests': 0,
                'total_time': 0.0,
                'avg_response_time': 0.0,
                'errors': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'parallel_requests': 0
            })
            self._lock = self._manager.Lock()
        else:
            self._metrics: Dict[str, Any] = {
                'requests': 0,
                'total_time': 0.0,
                'avg_response_time': 0.0,
                'errors': 0,
                'cache_hits': 0,
                'cache_misses': 0,
                'parallel_requests': 0
            }
            self._lock = threading.Lock()
        
        self._start_time = time.time()
    
    def record_request(self, response_time: float, error: bool = False, 
                      cache_hit: bool = False, is_parallel: bool = False):
        """Record request metrics"""
        with self._lock:
            self._metrics['requests'] += 1
            self._metrics['total_time'] += response_time
            self._metrics['avg_response_time'] = self._metrics['total_time'] / self._metrics['requests']
            
            if error:
                self._metrics['errors'] += 1
            
            if cache_hit:
                self._metrics['cache_hits'] += 1
            else:
                self._metrics['cache_misses'] += 1
            
            if is_parallel:
                self._metrics['parallel_requests'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current metrics"""
        with self._lock:
            uptime = time.time() - self._start_time
            cache_total = self._metrics['cache_hits'] + self._metrics['cache_misses']
            cache_hit_rate = (self._metrics['cache_hits'] / max(cache_total, 1)) * 100
            
            metrics_dict = dict(self._metrics) if self.use_multiprocess else self._metrics.copy()
            
            return {
                **metrics_dict,
                'uptime_seconds': uptime,
                'cache_hit_rate': f"{cache_hit_rate:.1f}%",
                'error_rate': f"{(metrics_dict['errors'] / max(metrics_dict['requests'], 1)) * 100:.1f}%",
                'parallel_ratio': f"{(metrics_dict['parallel_requests'] / max(metrics_dict['requests'], 1)) * 100:.1f}%"
            }
    
    def reset_metrics(self):
        """Reset all metrics"""
        with self._lock:
            if self.use_multiprocess:
                self._metrics.clear()
                self._metrics.update({
                    'requests': 0,
                    'total_time': 0.0,
                    'avg_response_time': 0.0,
                    'errors': 0,
                    'cache_hits': 0,
                    'cache_misses': 0,
                    'parallel_requests': 0
                })
            else:
                self._metrics = {
                    'requests': 0,
                    'total_time': 0.0,
                    'avg_response_time': 0.0,
                    'errors': 0,
                    'cache_hits': 0,
                    'cache_misses': 0,
                    'parallel_requests': 0
                }
            self._start_time = time.time()

# Global performance monitors
performance_monitor = PerformanceMonitor(use_multiprocess=False)
multiprocess_performance_monitor = PerformanceMonitor(use_multiprocess=True)

def get_system_status(use_multiprocess: bool = True) -> Dict[str, Any]:
    """Get comprehensive system status"""
    if use_multiprocess:
        container = get_multiprocess_container()
        monitor = multiprocess_performance_monitor
    else:
        container = get_container()
        monitor = performance_monitor
    
    config = get_config()
    
    status = {
        'services': container.get_health_status(),
        'performance': monitor.get_metrics(),
        'dependencies': DependencyValidator.validate_all(),
        'config_sources': {
            key: config.get_config_source(key).value if config.get_config_source(key) else 'unknown'
            for key in ['ollama.url', 'speech.tts_engine', 'audio.player']
        },
        'resource_usage': {
            'registered_resources': len(resource_manager._resources),
            'cleanup_callbacks': len(resource_manager._cleanup_callbacks)
        },
        'multiprocess_info': {
            'cpu_count': mp.cpu_count(),
            'current_process_id': mp.current_process().pid,
            'use_multiprocess': use_multiprocess
        }
    }
    
    if use_multiprocess:
        try:
            status['performance_stats'] = container.get_performance_stats()
        except Exception as e:
            status['performance_stats'] = {'error': f'Failed to get stats: {e}'}
    
    return status

def print_system_status(use_multiprocess: bool = True):
    """Print formatted system status"""
    status = get_system_status(use_multiprocess)
    
    mode = "MULTIPROCESS" if use_multiprocess else "THREADING"
    _print_header(mode)
    _print_system_info(status['multiprocess_info'])
    _print_services_status(status['services'])
    _print_performance_metrics(status['performance'])
    _print_dependencies_status(status['dependencies'])
    _print_resource_usage(status['resource_usage'])
    
    logger = logging.getLogger("system_status")
    if use_multiprocess and 'performance_stats' in status:
        _print_detailed_performance(status['performance_stats'])
    logger.info(f"{'=' * 60}")

def _print_header(mode: str):
    """Print status header"""
    logger = logging.getLogger("system_status")
    logger.info(f"\n{'=' * 60}")
    logger.info(f"ZORGLUB AI - SYSTEM STATUS ({mode})")
    logger.info(f"{'=' * 60}")

def _print_system_info(mp_info: Dict[str, Any]):
    """Print system information"""
    logger = logging.getLogger("system_status")
    logger.info("\n SYSTEM INFO:")
    logger.info(f"  CPU Count: {mp_info['cpu_count']}")
    logger.info(f"  Process ID: {mp_info['current_process_id']}")
    logger.info(f"  Mode: {'Multiprocessing' if mp_info['use_multiprocess'] else 'Threading'}")

def _print_services_status(services: Dict[str, Any]):
    """Print services status"""
    logger = logging.getLogger("system_status")
    logger.info("\n SERVICES:")
    logger.info(f"  Initialized: {'ok' if services['initialized'] else 'no'}")
    for service, health in services['services'].items():
        logger.info(f"  {service}: {'ok' if health else 'no'}")

def _print_performance_metrics(perf: Dict[str, Any]):
    """Print performance metrics"""
    logger = logging.getLogger("system_status")
    logger.info("\n PERFORMANCE:")
    logger.info(f"  Requests: {perf['requests']}")
    logger.info(f"  Avg Response Time: {perf['avg_response_time']:.2f}s")
    logger.info(f"  Cache Hit Rate: {perf['cache_hit_rate']}")
    logger.info(f"  Error Rate: {perf['error_rate']}")
    logger.info(f"  Parallel Ratio: {perf['parallel_ratio']}")
    logger.info(f"  Uptime: {perf['uptime_seconds']:.0f}s")

def _print_dependencies_status(dependencies: Dict[str, bool]):
    """Print dependencies status"""
    logger = logging.getLogger("system_status")
    logger.info("\n DEPENDENCIES:")
    for dep, status_ok in dependencies.items():
        logger.info(f"  {dep}: {'ok' if status_ok else 'no'}")

def _print_resource_usage(res: Dict[str, Any]):
    """Print resource usage"""
    logger = logging.getLogger("system_status")
    logger.info("\n RESOURCES:")
    logger.info(f"  Registered Resources: {res['registered_resources']}")
    logger.info(f"  Cleanup Callbacks: {res['cleanup_callbacks']}")

def _print_detailed_performance(perf_stats: Dict[str, Any]):
    """Print detailed performance stats"""
    logger = logging.getLogger("system_status")
    logger.info("\n  DETAILED PERFORMANCE:")
    for service, stats in perf_stats.items():
        if isinstance(stats, dict) and 'error' not in stats:
            _print_service_stats(service, stats)

def _print_nested_stats(value_dict: Dict[str, Any]):
    """Print nested statistics"""
    logger = logging.getLogger("system_status")
    for subkey, subval in value_dict.items():
        logger.info(f"    {subkey}: {subval}")

def _print_service_stats(service: str, stats: Dict[str, Any]):
    """Print stats for a single service"""
    logger = logging.getLogger("system_status")
    logger.info(f"  {service.upper()}:")
    for key, value in stats.items():
        if isinstance(value, dict):
            _print_nested_stats(value)
        else:
            logger.info(f"    {key}: {value}")

# Convenience functions
def quick_start(use_multiprocess: bool = True) -> bool:
    mode = "multiprocessing" if use_multiprocess else "threading"
    logger = logging.getLogger("quick_start")
    logger.info(f"Starting Zorglub AI with {mode}...")
    
    if use_multiprocess:
        success = initialize_multiprocess_services()
    else:
        success = initialize_services()
    
    if success:
        print_system_status(use_multiprocess)
        logger.info(f"\n Zorglub AI is ready with {mode}!")
        return True
    else:
        logger.warning("\n  Some services failed to start")
        print_system_status(use_multiprocess)
        return False

def quick_test(use_multiprocess: bool = True):
    mode = "multiprocessing" if use_multiprocess else "threading"
    logger = logging.getLogger("quick_test")
    logger.info(f"Testing Zorglub AI services with {mode}...")
    
    try:
        # Test AI service
        if use_multiprocess:
            ai_client = get_multiprocess_ai_client()
        else:
            ai_client = get_ai_client()
        response = ai_client.ask("Hello, can you respond briefly?", use_cache=False)
        logger.info(f"AI Service: {response[:50]}...")
        # Test STT service
        if use_multiprocess:
            get_multiprocess_stt_service()
        else:
            get_stt_service()
        logger.info("STT Service: Ready")
        # Test TTS service
        if use_multiprocess:
            get_multiprocess_tts_service()
        else:
            get_tts_service()
        logger.info("TTS Service: Ready")
        logger.info(f"\n All services are working with {mode}!")
    except Exception as e:
        logger.error(f"\n Service test failed: {e}")

def benchmark_performance():
    """Benchmark performance comparison antara threading vs multiprocessing"""
    logger = logging.getLogger("benchmark_performance")
    logger.info("Starting performance benchmark...")
    # Test dengan threading
    logger.info("\n Testing with Threading...")
    start_time = time.time()
    quick_test(use_multiprocess=False)
    threading_time = time.time() - start_time
    # Test dengan multiprocessing
    logger.info("\n Testing with Multiprocessing...")
    start_time = time.time()
    quick_test(use_multiprocess=True)
    multiprocess_time = time.time() - start_time
    # Compare results
    logger.info("\n BENCHMARK RESULTS:")
    logger.info(f"  Threading Time: {threading_time:.2f}s")
    logger.info(f"  Multiprocessing Time: {multiprocess_time:.2f}s")
    if multiprocess_time < threading_time:
        improvement = ((threading_time - multiprocess_time) / threading_time) * 100
        logger.info(" Multiprocessing is %.1f%% faster!", improvement)
    else:
        degradation = ((multiprocess_time - threading_time) / threading_time) * 100
        logger.info(" Multiprocessing is %.1f%% slower", degradation)

# Export main components
__all__ = [
    # Container (both)
    'get_container',
    'get_multiprocess_container',
    'initialize_services',
    'initialize_multiprocess_services',
    'shutdown_services',
    'shutdown_multiprocess_services',
    'managed_services',
    'managed_multiprocess_services',
    
    # Configuration
    'get_config',
    'EnhancedConfig',
    'OllamaConfig',
    'SpeechConfig',
    'AudioConfig',
    'PerformanceConfig',
    
    # Services (regular)
    'get_ai_client',
    'get_stt_service',
    'get_tts_service',
    
    # Services (multiprocess)
    'get_multiprocess_ai_client',
    'get_multiprocess_stt_service',
    'get_multiprocess_tts_service',
    
    # Adapters
    'AIServiceAdapter',
    'SpeechToTextAdapter',
    'TextToSpeechAdapter',
    'get_enhanced_ai_service',
    'get_enhanced_stt_service',
    'get_enhanced_tts_service',
    
    # Monitoring
    'performance_monitor',
    'multiprocess_performance_monitor',
    'get_system_status',
    'print_system_status',
    
    # Convenience
    'quick_start',
    'quick_test',
    'benchmark_performance',
    
    # Resource management
    'resource_manager',
    'DependencyValidator'
]
