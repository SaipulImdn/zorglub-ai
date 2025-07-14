import requests
import json
import time
import multiprocessing as mp
import pickle
import hashlib
from typing import Dict, Any, Optional, List, Tuple
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ProcessPoolExecutor, as_completed

from shared.config import Config
from .multiprocess_base import (
    ServiceFactory, MultiprocessSingletonMixin, ProcessPool, 
    ProcessSafeQueue, resource_manager, process_worker_initializer
)

def make_ollama_request(request_data: Tuple[str, Dict, Dict]) -> Tuple[str, str, bool]:
    url, payload, config = request_data
    
    try:
        session = requests.Session()
        retry_strategy = Retry(
            total=config.get('max_retries', 3),
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        response = session.post(
            url,
            json=payload,
            timeout=config.get('timeout', 120)
        )
        
        if response.status_code != 200:
            return "", f"Error: Ollama server returned status {response.status_code}", True
        
        data = response.json()
        
        if 'message' in data and 'content' in data['message']:
            content = data['message']['content']
        elif 'response' in data:
            content = data['response']
        else:
            content = f"Unexpected response format: {data}"
        
        return content, "", False
        
    except requests.exceptions.ConnectionError:
        return "", "Error: Ollama server is not running. Please start Ollama first.", True
    except requests.exceptions.Timeout:
        return "", "Error: Request timed out. Please try again.", True
    except Exception as e:
        return "", f"Error: {str(e)}", True

class MultiprocessResponseCache:
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self._manager = mp.Manager()
        self._cache = self._manager.dict()
        self._timestamps = self._manager.dict()
        self._max_size = max_size
        self._ttl = ttl
        self._lock = self._manager.Lock()
    
    def _generate_key(self, messages: List[Dict], options: Dict = None) -> str:
        key_data = {
            'messages': messages,
            'options': options or {}
        }
        key_string = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, messages: List[Dict], options: Dict = None) -> Optional[str]:
        key = self._generate_key(messages, options)
        
        with self._lock:
            if key in self._cache:
                timestamp = self._timestamps.get(key, 0)
                if time.time() - timestamp < self._ttl:
                    return self._cache[key]
                else:
                    del self._cache[key]
                    if key in self._timestamps:
                        del self._timestamps[key]
        
        return None
    
    def set(self, messages: List[Dict], response: str, options: Dict = None):
        key = self._generate_key(messages, options)
        current_time = time.time()
        
        with self._lock:
            if len(self._cache) >= self._max_size:
                oldest_key = min(self._timestamps.keys(), 
                               key=lambda k: self._timestamps[k])
                del self._cache[oldest_key]
                del self._timestamps[oldest_key]
            
            self._cache[key] = response
            self._timestamps[key] = current_time
    
    def clear(self):
        with self._lock:
            self._cache.clear()
            self._timestamps.clear()

class MultiprocessOllamaClient:
    def __init__(self, max_workers: Optional[int] = None):
        self.config = Config.get_ollama_settings()
        self.max_workers = max_workers or min(4, mp.cpu_count())
        self.cache = MultiprocessResponseCache()
        
        self._manager = mp.Manager()
        self._stats = self._manager.dict({
            'requests': 0,
            'cache_hits': 0,
            'errors': 0,
            'parallel_requests': 0
        })
        
        self.request_queue = ProcessSafeQueue(maxsize=100)
        self.response_queue = ProcessSafeQueue(maxsize=100)
    
    def ask(self, prompt: str, use_cache: bool = True) -> str:
        messages = [{"role": "user", "content": prompt}]
        return self._make_request(messages, use_cache=use_cache)
    
    def ask_with_context(self, messages: List[Dict], options: Dict = None, use_cache: bool = True) -> str:
        return self._make_request(messages, options=options, use_cache=use_cache)
    
    def ask_batch(self, prompts: List[str], use_cache: bool = True) -> List[str]:
        if not prompts:
            return []
        
        batch_messages = [
            [{"role": "user", "content": prompt}] 
            for prompt in prompts
        ]
        
        return self._make_batch_requests(batch_messages, use_cache=use_cache)
    
    def _make_request(self, messages: List[Dict], options: Dict = None, use_cache: bool = True) -> str:
        self._stats['requests'] += 1
        
        if use_cache:
            cached_response = self.cache.get(messages, options)
            if cached_response:
                self._stats['cache_hits'] += 1
                return cached_response
        
        payload = {
            "model": self.config['model'],
            "messages": messages,
            "stream": False
        }
        
        if options:
            payload["options"] = options
        
        request_data = (self.config['url'], payload, self.config)
        
        try:
            content, error, is_error = make_ollama_request(request_data)
            
            if is_error:
                self._stats['errors'] += 1
                return error
            
            if use_cache and content:
                self.cache.set(messages, content, options)
            
            return content
            
        except Exception as e:
            self._stats['errors'] += 1
            return f"Error: {str(e)}"
    
    def _make_batch_requests(self, batch_messages: List[List[Dict]], 
                           options: Dict = None, use_cache: bool = True) -> List[str]:
        if not batch_messages:
            return []
        
        self._stats['parallel_requests'] += 1
        
        cached_responses, uncached_requests = self._process_cache_for_batch(
            batch_messages, options, use_cache
        )
        
        new_results = self._execute_parallel_requests(
            uncached_requests, batch_messages, options, use_cache
        )
        
        return self._combine_batch_results(
            batch_messages, cached_responses, new_results
        )
    
    def _process_cache_for_batch(self, batch_messages: List[List[Dict]], 
                               options: Dict = None, use_cache: bool = True) -> Tuple[Dict[int, str], List[Tuple[int, List[Dict]]]]:
        cached_responses = {}
        uncached_requests = []
        
        if use_cache:
            for i, messages in enumerate(batch_messages):
                cached = self.cache.get(messages, options)
                if cached:
                    cached_responses[i] = cached
                    self._stats['cache_hits'] += 1
                else:
                    uncached_requests.append((i, messages))
        else:
            uncached_requests = list(enumerate(batch_messages))
        
        return cached_responses, uncached_requests
    
    def _execute_parallel_requests(self, uncached_requests: List[Tuple[int, List[Dict]]], 
                                 batch_messages: List[List[Dict]], options: Dict = None, 
                                 use_cache: bool = True) -> Dict[int, str]:
        results = {}
        
        if not uncached_requests:
            return results
        
        request_data_list = self._prepare_request_data(uncached_requests, options)
        
        with ProcessPool(
            max_workers=min(self.max_workers, len(request_data_list)),
            initializer=process_worker_initializer
        ) as pool:
            results = self._submit_and_collect_requests(
                pool, uncached_requests, request_data_list, 
                batch_messages, options, use_cache
            )
        
        return results
    
    def _prepare_request_data(self, uncached_requests: List[Tuple[int, List[Dict]]], 
                            options: Dict = None) -> List[Tuple[str, Dict, Dict]]:
        request_data_list = []
        
        for _, messages in uncached_requests:
            payload = {
                "model": self.config['model'],
                "messages": messages,
                "stream": False
            }
            
            if options:
                payload["options"] = options
            
            request_data_list.append((self.config['url'], payload, self.config))
        
        return request_data_list
    
    def _submit_and_collect_requests(self, pool: ProcessPool, 
                                   uncached_requests: List[Tuple[int, List[Dict]]], 
                                   request_data_list: List[Tuple[str, Dict, Dict]], 
                                   batch_messages: List[List[Dict]], 
                                   options: Dict = None, use_cache: bool = True) -> Dict[int, str]:
        results = {}
        
        futures = {}
        for idx, (request_idx, _) in enumerate(uncached_requests):
            future = pool.submit(make_ollama_request, request_data_list[idx])
            futures[future] = request_idx
        
        for future in as_completed(futures.keys(), timeout=self.config['timeout'] + 10):
            request_idx = futures[future]
            try:
                content, error, is_error = future.result()
                
                if is_error:
                    self._stats['errors'] += 1
                    results[request_idx] = error
                else:
                    results[request_idx] = content
                    
                    if use_cache and content:
                        messages = batch_messages[request_idx]
                        self.cache.set(messages, content, options)
            
            except Exception as e:
                self._stats['errors'] += 1
                results[request_idx] = f"Error: {str(e)}"
        
        return results
    
    def _combine_batch_results(self, batch_messages: List[List[Dict]], 
                             cached_responses: Dict[int, str], 
                             new_results: Dict[int, str]) -> List[str]:
        final_results = []
        
        for i in range(len(batch_messages)):
            if i in cached_responses:
                final_results.append(cached_responses[i])
            elif i in new_results:
                final_results.append(new_results[i])
            else:
                final_results.append("Error: No response received")
        
        return final_results
    
    def get_stats(self) -> Dict:
        stats_dict = dict(self._stats)
        total_requests = max(stats_dict['requests'], 1)
        cache_hit_rate = (stats_dict['cache_hits'] / total_requests) * 100
        error_rate = (stats_dict['errors'] / total_requests) * 100
        
        return {
            **stats_dict,
            'cache_hit_rate': f"{cache_hit_rate:.1f}%",
            'error_rate': f"{error_rate:.1f}%"
        }
    
    def clear_cache(self):
        self.cache.clear()
    
    def shutdown(self):
        try:
            self.clear_cache()
        except Exception as e:
            print(f"Error during shutdown: {e}")

class MultiprocessAIServiceFactory(ServiceFactory[MultiprocessOllamaClient], MultiprocessSingletonMixin):
    def create(self, max_workers: Optional[int] = None, **kwargs) -> MultiprocessOllamaClient:
        client = MultiprocessOllamaClient(max_workers=max_workers)
        resource_manager.register_resource(client, client.shutdown)
        return client
    
    def validate_dependencies(self) -> bool:
        try:
            session = requests.Session()
            response = session.get(
                "http://localhost:11434/api/version", 
                timeout=5
            )
            session.close()
            return response.status_code == 200
            
        except Exception:
            return False

_ai_client: Optional[MultiprocessOllamaClient] = None
_factory: Optional[MultiprocessAIServiceFactory] = None

def get_multiprocess_ai_client(max_workers: Optional[int] = None) -> MultiprocessOllamaClient:
    global _ai_client, _factory
    
    if _ai_client is None:
        if _factory is None:
            _factory = MultiprocessAIServiceFactory()
        _ai_client = _factory.create(max_workers=max_workers)
    
    return _ai_client

def shutdown_ai_client():
    global _ai_client
    if _ai_client:
        _ai_client.shutdown()
        _ai_client = None
