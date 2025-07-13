from flask import Flask, request, jsonify, render_template, send_file
from flask_cors import CORS
import os
import tempfile
import io
from core.use_cases.interact import interact_with_ai_web
from core.interfaces.speech_input import SpeechToText
from core.interfaces.ai_service import AIService
from core.interfaces.speech_output import TextToSpeech

app = Flask(__name__)
CORS(app)

# Initialize services
stt = SpeechToText()
ai_service = AIService()
tts = TextToSpeech()

@app.route('/')
def index():
    return render_template('demo.html')

@app.route('/api/process-voice', methods=['POST'])
def process_voice():
    try:
        if 'audio' not in request.files:
            return jsonify({'error': 'No audio file provided'}), 400
        
        audio_file = request.files['audio']
        
        # Save temporary audio file
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as tmp_file:
            audio_file.save(tmp_file.name)
            
            # Process speech to text
            user_input = stt.transcribe_file(tmp_file.name)
            
            if user_input:
                # Get AI response
                ai_response = ai_service.ask(user_input)
                
                # Clean up temp file
                os.unlink(tmp_file.name)
                
                return jsonify({
                    'user_text': user_input,
                    'ai_text': ai_response,
                    'success': True
                })
            else:
                os.unlink(tmp_file.name)
                return jsonify({'error': 'Could not transcribe audio'}), 400
                
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/text-to-speech', methods=['POST'])
def text_to_speech():
    try:
        data = request.get_json()
        text = data.get('text', '')
        
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        
        # Generate audio file
        audio_file = tts.generate_audio_file(text)
        
        return send_file(
            audio_file,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name='response.mp3'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/text-only', methods=['POST'])
def text_only():
    try:
        data = request.get_json()
        user_input = data.get('text', '')
        
        if not user_input:
            return jsonify({'error': 'No text provided'}), 400
        
        # Get AI response
        ai_response = ai_service.ask(user_input)
        
        return jsonify({
            'user_text': user_input,
            'ai_text': ai_response,
            'success': True
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
