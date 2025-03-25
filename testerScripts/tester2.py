import threading
import time
import os
import subprocess
import json
import numpy as np
import sounddevice as sd
import parselmouth
from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from pythonosc.udp_client import SimpleUDPClient
from pythonosc import osc_message_builder, osc_bundle_builder
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Create UDP client to send pitch to chuck code
client = SimpleUDPClient("127.0.0.1", 6449)
hmin = 100
hmax = 300
vmin = 80
vmax = 400
fs = 44100
config = ""

intensityFactor = 1.5
pitchFactor = 1.0
time_window = 0
duration = 0
waveform_shape = ""

app = Flask(__name__)
CORS(app)

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    logging.error("config.json not found. Using default values.")
    config = {
        'chuck_script': './chuckScripts/hapticize.ck',
        'default_intensity': 50,
        'default_duration': 250,  # milliseconds
        'udp_ip': '127.0.0.1', # IP to send UDP packets to
        'udp_port': 6449 # Port to send UDP packets to
    }

chuck_process = None  # Global variable to store the Chuck process
chuck_lock = threading.Lock()

def start_chuck():
    global chuck_process, hapticizing, audio_thread, chuck_lock
    hapticizing = True
    logging.debug("inside start")
    with chuck_lock:
        logging.debug("inside lock")
        if chuck_process is None:
            logging.debug("inside if")
            try:
                if not os.path.exists(config['chuck_script']):
                    logging.error(f"Chuck script not found: {config['chuck_script']}")
                logging.debug("hello")
                chuck_process = subprocess.Popen(['chuck', config['chuck_script']],
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
                logging.debug(f"STARTED {chuck_process}")
                return True
            except Exception as e:
                logging.error(f"Error starting Chuck: {e}")
                return False
        else:
            logging.debug("um")

def stop_chuck():
    global chuck_process, chuck_lock
    with chuck_lock:
        if chuck_process:
            chuck_process.terminate()  # Or .kill() if needed
            chuck_process.wait() # Make sure the process has fully stopped
            chuck_process = None
            logging.debug("Chuck stopped.")

# @app.before_request
# def before_request():
#     # Add your before request logic here
#     pass

# @app.teardown_appcontext
# def teardown_appcontext(exception):
#     if chuck_process is not None:
#         logging.debug("why would i be here")
#         stop_chuck()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_hapticize', methods=['POST'])
def start_hapticize():
    global hapticizing, chuck_process, audio_thread
    if chuck_process is None:
        start_chuck()
    hapticizing = True
    logging.debug("inside start hapticize")
    logging.debug(f"chuck process {chuck_process}")
    if chuck_process is not None:
        logging.debug("chuck started")
    else:
        logging.error("CHUCK NOT STARTED")

    return jsonify({'status': 'Hapticizing started'})

@app.route('/stop_hapticize', methods=['POST'])
def stop_hapticize():
    global hapticizing, chuck_process
    hapticizing = False
    stop_chuck()
    chuck_process = None
    return jsonify({'status': 'Hapticizing stopped'})

@app.route('/shutdown')
def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()
    return "Server shutting down..."

@app.route('/modulation', methods=['POST'])
def modulation():
    try:
        data = request.get_json()  # Get the JSON data from the request body

        # Extract the modulation parameters from the JSON data
        intensityFactor = data.get('intensity')
        pitchFactor = data.get('pitch')
        time_window = data.get('timeWindow')
        duration = data.get('duration')
        waveform_shape = data.get('waveformShape')

        bundle = osc_bundle_builder.OscBundleBuilder(osc_bundle_builder.IMMEDIATELY)

        msg = osc_message_builder.OscMessageBuilder(address="/modulation/bundle")
        msg.add_arg(intensityFactor)
        msg.add_arg(pitchFactor)
        msg.add_arg(time_window)
        msg.add_arg(duration)
        msg.add_arg(waveform_shape)
        bundle.add_content(msg.build())

        client.send(bundle.build())

        logging.debug("SENT BUNDLE")

        # Example: Print the received parameters to the console
        logging.debug("Received modulation parameters:")
        logging.debug(f"Intensity: {intensityFactor}")
        logging.debug(f"Pitch: {pitchFactor}")
        logging.debug(f"Time Window: {time_window}")
        logging.debug(f"Duration: {duration}")
        logging.debug(f"Waveform Shape: {waveform_shape}")

        return jsonify({'status': 'Modulation parameters received'}), 200  # Return a success response

    except Exception as e:
        logging.error(f"Error processing modulation parameters: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/vibrate', methods=['POST'])
def vibrate():
    try:
        data = request.get_json()
        intensity_exaggeration = float(data.get('intensityExaggeration', 1.0)) # Get modulation values
        pitch_exaggeration = float(data.get('pitchExaggeration', 1.0))
        time_window = int(data.get('timeWindow', 250))
        waveform_shape = data.get('waveformShape', 'sine')

        modintensity = intensity * intensity_exaggeration
        modpitch = pitch * pitch_exaggeration

        result = detect_and_send_pitch(modintensity, modpitch) # call the function
        if "Error:" not in result: # If there's no error in the function
            return jsonify({'status': 'vibrating', 'intensity': intensity, 'pitch': pitch, 'form': waveform_shape})
        else:
            return jsonify({'status': 'error', 'message': result}), 500 # If there's an error

    except Exception as e:
        logging.error(f"Error in /vibrate route: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

def detect_and_send_pitch(audio, sample_rate):
    try:
        sound = parselmouth.Sound(audio, sampling_frequency=sample_rate)
        rms = sound.get_rms()
        intensity = sound.get_intensity()

        pitch = sound.to_pitch(pitch_floor=120)
        pitch_values = pitch.selected_array['frequency']

        total = 0.0
        valid = 0

        for value in pitch_values:
            if value != 0:
                total += value
                valid += 1

        if valid > 0:
            value = total / valid
        else:
            value = 0

        vmin = 80
        vmax = 400
        if value > vmin and value < vmax and intensity > 30:
            hmin = 100
            hmax = 300
            normalized_pitch = hmin + ((value - vmin) / (vmax - vmin)) * hmax
            client.send_message("/pitch", normalized_pitch * pitchFactor)

        if intensity > 30:
            normalized_intensity = (intensity - 30) / (100 - 30)
            client.send_message("/loudness", normalized_intensity * 1.5)
            logging.debug(f"normal: {normalized_intensity}, augmented: {normalized_intensity * intensityFactor}")
    except Exception as e:
        logging.error(f"Error in detect_and_send_pitch: {e}")

def audio_callback(indata, frames, time, status):
    if status:
        logging.error(status)
        return
    
    mono_audio = np.mean(indata, axis=1)
    detect_and_send_pitch(mono_audio, fs)

def audio_thread_function():
    duration = int(fs * 0.5)

    with sd.InputStream(channels=1, samplerate=fs, blocksize=duration, callback=audio_callback) as stream:
        logging.debug("Listening (audio thread)...")
        while True:
            time.sleep(0.1)

audio_thread = threading.Thread(target=audio_thread_function)
audio_thread.daemon = True
audio_thread.start()
app.run(debug=True, use_reloader=False)
logging.debug(threading.enumerate())
logging.debug("stream closed? idk girl")
if chuck_process is not None:
    stop_chuck()