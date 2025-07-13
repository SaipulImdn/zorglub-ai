from core.interfaces.speech_input import SpeechToText
from core.interfaces.ai_service import AIService
from core.interfaces.speech_output import TextToSpeech

def interact_with_ai_web(user_input: str):
    """Web version of AI interaction that takes text input directly"""
    ai = AIService()

    response = ai.ask(user_input)
    return {
        'user_text': user_input,
        'ai_text': response
    }

def interact_with_ai():
    """Original CLI version"""
    stt = SpeechToText()
    ai = AIService()
    tts = TextToSpeech()

    print("Silakan bicara...")
    user_input = stt.listen()
    if user_input:
        print(f"Anda: {user_input}")
        response = ai.ask(user_input)
        print(f"AI: {response}")
        tts.speak(response)
