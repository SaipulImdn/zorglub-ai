import requests
import json
import asyncio
import threading
import time
from typing import Dict, Any, Optional, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.poolmanager import PoolManager

from shared.config import Config
from .base_factory import ServiceFactory, SingletonMixin, resource_manager

class ConnectionPool:
    
    def __init__(self, pool_size: int = 10, max_retries: int = 3):
        self.session = requests.Session()
        
        retry_strategy = Retry(
            total=max_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
            backoff_factor=1
        )
        
        adapter = HTTPAdapter(
            pool_connections=pool_size,
            pool_maxsize=pool_size,
            max_retries=retry_strategy
        )
        
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        self.session.timeout = (5, 30)
        
        resource_manager.register_resource(self.session, self.cleanup)
    
    def post(self, url: str, **kwargs) -> requests.Response:
        return self.session.post(url, **kwargs)
    
    def get(self, url: str, **kwargs) -> requests.Response:
        return self.session.get(url, **kwargs)
    
    def cleanup(self):
        if hasattr(self, 'session'):
            self.session.close()

class ResponseCache:
    
    def __init__(self, max_size: int = 100, ttl: int = 300):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._max_size = max_size
        self._ttl = ttl
        self._lock = threading.RLock()
    
    def get(self, key: str) -> Optional[str]:
        with self._lock:
            if key in self._cache:
                entry = self._cache[key]
                if time.time() - entry['timestamp'] < self._ttl:
                    return entry['response']
                else:
                    del self._cache[key]
            return None
    
    def set(self, key: str, response: str):
        with self._lock:
            if len(self._cache) >= self._max_size:
                oldest_key = min(self._cache.keys(), 
                               key=lambda k: self._cache[k]['timestamp'])
                del self._cache[oldest_key]
            
            self._cache[key] = {
                'response': response,
                'timestamp': time.time()
            }
    
    def clear(self):
        with self._lock:
            self._cache.clear()

class OllamaClient:
    
    def __init__(self):
        self.config = Config.get_ollama_settings()
        self.connection_pool = ConnectionPool()
        self.cache = ResponseCache()
        self._stats = {
            'requests': 0,
            'cache_hits': 0,
            'errors': 0
        }
    
    def _generate_cache_key(self, messages: List[Dict], options: Dict = None) -> str:
        key_data = {
            'messages': messages,
            'model': self.config['model'],
            'options': options or {}
        }
        return str(hash(json.dumps(key_data, sort_keys=True)))
    
    def ask(self, prompt: str, use_cache: bool = True) -> str:
        messages = [{"role": "user", "content": prompt}]
        return self._make_request(messages, use_cache=use_cache)
    
    def ask_with_context(self, messages: List[Dict], options: Dict = None, use_cache: bool = True) -> str:
        return self._make_request(messages, options=options, use_cache=use_cache)
    
    def _make_request(self, messages: List[Dict], options: Dict = None, use_cache: bool = True) -> str:
        self._stats['requests'] += 1
        
        if use_cache:
            cache_key = self._generate_cache_key(messages, options)
            cached_response = self.cache.get(cache_key)
            if cached_response:
                self._stats['cache_hits'] += 1
                return cached_response
        
        try:
            payload = {
                "model": self.config['model'],
                "messages": messages,
                "stream": False
            }
            
            if options:
                payload["options"] = options
            
            response = self.connection_pool.post(
                self.config['url'],
                json=payload,
                timeout=self.config['timeout']
            )
            
            if response.status_code != 200:
                self._stats['errors'] += 1
                return f"Error: Ollama server returned status {response.status_code}"
            
            data = response.json()
            
            content = self._extract_content(data)
            
            if use_cache:
                self.cache.set(cache_key, content)
            
            return content
            
        except requests.exceptions.ConnectionError:
            self._stats['errors'] += 1
            return "Error: Ollama server is not running. Please start Ollama first."
        except requests.exceptions.Timeout:
            self._stats['errors'] += 1
            return "Error: Request timed out. Please try again."
        except Exception as e:
            self._stats['errors'] += 1
            return f"Error: {str(e)}"
    
    def _extract_content(self, data: Dict) -> str:
        if 'message' in data and 'content' in data['message']:
            return data['message']['content']
        elif 'response' in data:
            return data['response']
        else:
            return f"Unexpected response format: {data}"
    
    def get_stats(self) -> Dict:
        cache_hit_rate = (self._stats['cache_hits'] / max(self._stats['requests'], 1)) * 100
        return {
            **self._stats,
            'cache_hit_rate': f"{cache_hit_rate:.1f}%"
        }
    
    def clear_cache(self):
        self.cache.clear()

class AIServiceFactory(ServiceFactory[OllamaClient], SingletonMixin):
    
    def create(self, **kwargs) -> OllamaClient:
        return OllamaClient()
    
    def validate_dependencies(self) -> bool:
        try:
            pool = ConnectionPool()
            
            response = pool.get(
                "http://localhost:11434/api/version", 
                timeout=5
            )
            
            pool.cleanup()
            return response.status_code == 200
            
        except Exception:
            return False

_ai_client: Optional[OllamaClient] = None
_factory: Optional[AIServiceFactory] = None

def get_ai_client() -> OllamaClient:
    global _ai_client, _factory
    
    if _ai_client is None:
        if _factory is None:
            _factory = AIServiceFactory()
        _ai_client = _factory.create()
    
    return _ai_client
