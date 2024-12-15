from flask import Flask, request, jsonify, send_from_directory
import subprocess  # For running external scripts
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'  # Create this folder
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'audio' not in request.files:
        return jsonify({'error': 'No audio file part'}), 400
    file = request.files['audio']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], 'audio.wav')
    file.save(filepath)

    try:
        # Replace with your GitHub script's execution command
        #  This assumes your script is in a publicly accessible location and takes the file path as argument
        #  You'll likely need to adjust this based on how your script is deployed and how it takes input.
        process = subprocess.run(['python', 'chat_gpt_audio/test_chat.py', filepath], capture_output=True, text=True, check=True)
        transcription = process.stdout.strip()
        return jsonify({'transcription': transcription})
    except subprocess.CalledProcessError as e:
        return jsonify({'error': f'Error running transcription script: {e.stderr}'}), 500
    except FileNotFoundError:
        return jsonify({'error': 'Transcription script not found'}), 500

@app.route('/') # Add route to serve the index.html file
def serve_index():
    return send_from_directory('public', 'index.html')

if __name__ == '__main__':
    app.run(debug=True) #Set debug=False for production