import os
import json
import yaml
from typing import Dict, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

class ConfigSource(Enum):
    """Configuration source types"""
    ENVIRONMENT = "environment"
    FILE = "file"
    DEFAULT = "default"

@dataclass
class OllamaConfig:
    """Ollama service configuration"""
    url: str = "http://localhost:11434/api/chat"
    model: str = "llama3.1"
    timeout: int = 120
    max_retries: int = 3
    connection_pool_size: int = 10
    enable_cache: bool = True
    cache_ttl: int = 300  # 5 minutes

@dataclass
class SpeechConfig:
    """Speech processing configuration"""
    tts_language: str = "id"
    stt_language: str = "id"
    whisper_model: str = "base"
    tts_engine: str = "gtts"
    tts_voice: str = "id-ID-ArdiNeural"
    recording_duration: int = 5
    sample_rate: int = 16000
    max_segment_length: int = 200
    enable_parallel_processing: bool = True
    pause_between_segments: float = 0.3

@dataclass
class AudioConfig:
    """Audio processing configuration"""
    player: str = "mpv"
    enable_async_processing: bool = True
    max_workers: int = 4
    audio_buffer_size: float = 0.5
    audio_timeout: int = 30
    temp_dir: Optional[str] = None

@dataclass
class PerformanceConfig:
    """Performance optimization settings"""
    enable_model_cache: bool = True
    enable_connection_pooling: bool = True
    enable_response_cache: bool = True
    max_concurrent_requests: int = 5
    resource_cleanup_interval: int = 300  # 5 minutes

class ConfigManager:
    """Enhanced configuration manager"""
    
    def __init__(self, config_file: Optional[str] = None):
        self.config_file = config_file or self._find_config_file()
        self._config_cache: Dict[str, Any] = {}
        self._sources: Dict[str, ConfigSource] = {}
        
        # Load configurations
        self._load_configurations()
    
    def _find_config_file(self) -> Optional[str]:
        """Find configuration file dalam project"""
        possible_files = [
            "config.yaml",
            "config.yml",
            "config.json",
            ".zorglub.yaml",
            ".zorglub.yml"
        ]
        
        # Check in current directory dan parent directories
        current_dir = Path.cwd()
        for _ in range(5):  # Check up to 5 levels up
            for config_file in possible_files:
                config_path = current_dir / config_file
                if config_path.exists():
                    return str(config_path)
            current_dir = current_dir.parent
        
        return None
    
    def _load_configurations(self):
        """Load configurations dari multiple sources"""
        # 1. Load defaults
        self._load_defaults()
        
        # 2. Load from file
        if self.config_file:
            self._load_from_file()
        
        # 3. Load from environment
        self._load_from_environment()
    
    def _load_defaults(self):
        """Load default configurations"""
        defaults = {
            'ollama': asdict(OllamaConfig()),
            'speech': asdict(SpeechConfig()),
            'audio': asdict(AudioConfig()),
            'performance': asdict(PerformanceConfig())
        }
        
        for section, config in defaults.items():
            for key, value in config.items():
                config_key = f"{section}.{key}"
                self._config_cache[config_key] = value
                self._sources[config_key] = ConfigSource.DEFAULT
    
    def _load_from_file(self):
        """Load configuration dari file"""
        try:
            file_path = Path(self.config_file)
            
            if file_path.suffix.lower() in ['.yaml', '.yml']:
                with open(file_path, 'r') as f:
                    config_data = yaml.safe_load(f)
            elif file_path.suffix.lower() == '.json':
                with open(file_path, 'r') as f:
                    config_data = json.load(f)
            else:
                return
            
            # Flatten nested config
            self._flatten_config(config_data, source=ConfigSource.FILE)
            
        except Exception as e:
            print(f"Warning: Failed to load config file {self.config_file}: {e}")
    
    def _load_from_environment(self):
        """Load configuration dari environment variables"""
        env_mappings = {
            # Ollama
            'OLLAMA_URL': 'ollama.url',
            'OLLAMA_MODEL': 'ollama.model',
            'OLLAMA_TIMEOUT': 'ollama.timeout',
            
            # Speech
            'TTS_LANGUAGE': 'speech.tts_language',
            'STT_LANGUAGE': 'speech.stt_language',
            'WHISPER_MODEL': 'speech.whisper_model',
            'TTS_ENGINE': 'speech.tts_engine',
            'TTS_VOICE': 'speech.tts_voice',
            'RECORDING_DURATION': 'speech.recording_duration',
            'SAMPLE_RATE': 'speech.sample_rate',
            
            # Audio
            'AUDIO_PLAYER': 'audio.player',
            
            # Performance
            'ENABLE_CACHE': 'performance.enable_response_cache',
            'MAX_WORKERS': 'performance.max_concurrent_requests'
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert types
                converted_value = self._convert_env_value(env_value)
                self._config_cache[config_key] = converted_value
                self._sources[config_key] = ConfigSource.ENVIRONMENT
    
    def _flatten_config(self, config_data: Dict, prefix: str = "", source: ConfigSource = ConfigSource.FILE):
        """Flatten nested configuration"""
        for key, value in config_data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                self._flatten_config(value, full_key, source)
            else:
                self._config_cache[full_key] = value
                self._sources[full_key] = source
    
    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable value ke appropriate type"""
        # Boolean conversion
        if value.lower() in ['true', 'yes', '1', 'on']:
            return True
        elif value.lower() in ['false', 'no', '0', 'off']:
            return False
        
        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # Return as string
        return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self._config_cache.get(key, default)
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get all configuration untuk section"""
        prefix = f"{section}."
        return {
            k[len(prefix):]: v 
            for k, v in self._config_cache.items() 
            if k.startswith(prefix)
        }
    
    def get_ollama_config(self) -> OllamaConfig:
        """Get Ollama configuration object"""
        config_dict = self.get_section('ollama')
        return OllamaConfig(**config_dict)
    
    def get_speech_config(self) -> SpeechConfig:
        """Get Speech configuration object"""
        config_dict = self.get_section('speech')
        return SpeechConfig(**config_dict)
    
    def get_audio_config(self) -> AudioConfig:
        """Get Audio configuration object"""
        config_dict = self.get_section('audio')
        return AudioConfig(**config_dict)
    
    def get_performance_config(self) -> PerformanceConfig:
        """Get Performance configuration object"""
        config_dict = self.get_section('performance')
        return PerformanceConfig(**config_dict)
    
    def get_config_source(self, key: str) -> Optional[ConfigSource]:
        """Get source dari configuration value"""
        return self._sources.get(key)
    
    def set(self, key: str, value: Any, source: ConfigSource = ConfigSource.DEFAULT):
        """Set configuration value"""
        self._config_cache[key] = value
        self._sources[key] = source
    
    def save_to_file(self, file_path: str):
        """Save current configuration ke file"""
        # Group by sections
        sections = {}
        for key, value in self._config_cache.items():
            if '.' in key:
                section, config_key = key.split('.', 1)
                if section not in sections:
                    sections[section] = {}
                sections[section][config_key] = value
        
        # Save as YAML
        with open(file_path, 'w') as f:
            yaml.dump(sections, f, default_flow_style=False)
    
    def print_config(self):
        """Print current configuration dengan sources"""
        print("Current Configuration:")
        print("=" * 50)
        
        sections = {}
        for key, value in self._config_cache.items():
            if '.' in key:
                section, config_key = key.split('.', 1)
                if section not in sections:
                    sections[section] = {}
                sections[section][config_key] = {
                    'value': value,
                    'source': self._sources.get(key, ConfigSource.DEFAULT).value
                }
        
        for section, configs in sections.items():
            print(f"\n[{section.upper()}]")
            for key, info in configs.items():
                print(f"  {key}: {info['value']} ({info['source']})")

# Global config manager
_config_manager: Optional[ConfigManager] = None

def get_config() -> ConfigManager:
    """Get global configuration manager"""
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigManager()
    
    return _config_manager

# Backward compatibility
class EnhancedConfig:
    """Enhanced configuration class untuk backward compatibility"""
    
    @staticmethod
    def get_ollama_settings() -> Dict[str, Any]:
        """Get Ollama settings"""
        config = get_config().get_ollama_config()
        return {
            'url': config.url,
            'model': config.model,
            'timeout': config.timeout
        }
    
    @staticmethod
    def get_speech_settings() -> Dict[str, Any]:
        """Get speech settings"""
        config = get_config().get_speech_config()
        return asdict(config)
    
    @staticmethod
    def get_recording_settings() -> Dict[str, Any]:
        """Get recording settings"""
        config = get_config().get_speech_config()
        return {
            'duration': config.recording_duration,
            'sample_rate': config.sample_rate
        }
