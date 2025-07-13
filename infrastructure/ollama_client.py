import requests
import json
from shared.config import Config

def ask_gpt(prompt: str) -> str:
    try:
        settings = Config.get_ollama_settings()
        print(f"Sending request to Ollama with prompt: {prompt[:50]}...")
        
        response = requests.post(
            settings['url'],
            json={
                "model": settings['model'],
                "messages": [{"role": "user", "content": prompt}],
                "stream": False
            },
            timeout=settings['timeout']
        )
        
        print(f"Ollama response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Ollama error response: {response.text}")
            return f"Error: Ollama server returned status {response.status_code}"
        
        data = response.json()
        print(f"Ollama response data keys: {list(data.keys())}")
        
        # Try different response formats
        if 'message' in data and 'content' in data['message']:
            return data['message']['content']
        elif 'response' in data:
            return data['response']
        else:
            return f"Unexpected response format: {data}"
            
    except requests.exceptions.ConnectionError:
        print("Connection error: Ollama server is not running")
        return "Error: Ollama server is not running. Please start Ollama first."
    except requests.exceptions.Timeout:
        print("Timeout error: Ollama request timed out")
        return "Error: Request timed out. Please try again."
    except Exception as e:
        print(f"Error in ask_gpt: {str(e)}")
        return f"Error: {str(e)}"

def ask_gpt_with_context(context_prompt: str) -> str:
    """Enhanced ask_gpt with conversation context support"""
    try:
        settings = Config.get_ollama_settings()
        print(f"Sending contextual request to Ollama...")
        
        response = requests.post(
            settings['url'],
            json={
                "model": settings['model'],
                "messages": [{"role": "user", "content": context_prompt}],
                "stream": False,
                "options": {
                    "temperature": 0.7,  # More natural responses
                    "top_p": 0.9,       # Better context understanding
                    "num_ctx": 4096     # Larger context window
                }
            },
            timeout=settings['timeout']
        )
        
        print(f"Ollama response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Ollama error response: {response.text}")
            return f"Error: Ollama server returned status {response.status_code}"
        
        data = response.json()
        
        # Try different response formats
        if 'message' in data and 'content' in data['message']:
            return data['message']['content']
        elif 'response' in data:
            return data['response']
        else:
            return f"Unexpected response format: {data}"
            
    except requests.exceptions.ConnectionError:
        print("Connection error: Ollama server is not running")
        return "Error: Ollama server is not running. Please start Ollama first."
    except requests.exceptions.Timeout:
        print("Timeout error: Ollama request timed out")
        return "Error: Request timed out. Please try again."
    except Exception as e:
        print(f"Error in ask_gpt_with_context: {str(e)}")
        return f"Error: {str(e)}"
