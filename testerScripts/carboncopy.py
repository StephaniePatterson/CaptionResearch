import parselmouth
import time
import numpy as np
import speech_recognition as sr
import subprocess
from pythonosc.udp_client import SimpleUDPClient
import sounddevice as sd
import os
from flask_cors import CORS

from flask import Flask, request, jsonify, render_template, g
import json
import threading
import cProfile

# ADD:
# MESSAGE FOR CHANGING PITCH (done)
# AUDIO FILE PROCESSING SUPPORT + saving to audio file (done)
# INPUT/OUTPUT TIMESTAMP
# look at sampling size, make sure it is calculating correctly (yes, it's getting f1)
# have the hapticizer the same volume as speaker : NEED TO MAKE TIMEFRAME OF SOUND A LITTLE LONGER!!! (done)

# multiple options for how to process speech
# ideas: 
# - quiet mode / crowded room mode with different intensity thresholds
# - 

# Create UDP client to send pitch to chuck code
client = SimpleUDPClient("127.0.0.1", 6449)
hmin = 100
hmax = 300
vmin = 80
vmax = 400
fs = 44100

app = Flask(__name__)
CORS(app)

try:
    with open('config.json', 'r') as f:
        config = json.load(f)
except FileNotFoundError:
    print("Error: config.json not found. Using default values.")
    config = {
        'chuck_script': './chuckScripts/hapticize.ck',
        'default_intensity': 50,
        'default_duration': 1000,  # milliseconds
        'udp_ip': '127.0.0.1', # IP to send UDP packets to
        'udp_port': 6449 # Port to send UDP packets to
    }

chuck_process = None  # Global variable to store the Chuck process
chuck_lock = threading.Lock()

def start_chuck():
    global chuck_process, hapticizing, audio_thread
    hapticizing = True
    print("inside start")
    with chuck_lock:
        if chuck_process is None:
            print("inside if")
            try:
                
                if not os.path.exists(config['chuck_script']):
                    print(f"Chuck script not found: {config['chuck_script']}")
                print("hello")
                chuck_process = subprocess.Popen(['chuck', config['chuck_script']],
                                                stdout=subprocess.PIPE,
                                                stderr=subprocess.PIPE)
                print(chuck_process)
                return True
            except Exception as e:
                print(f"Error starting Chuck: {e}")
                return False
        else:
            print("um")

def stop_chuck():
    global chuck_process
    with chuck_lock:
        if chuck_process:
            chuck_process.terminate()  # Or .kill() if needed
            chuck_process.wait() # Make sure the process has fully stopped
            chuck_process = None
            print("Chuck stopped.")

# @app.before_request  # Use before_request instead
# def before_request():
#     global audio_thread
#     audio_thread = threading.Thread(target=audio_thread_function)
#     audio_thread.daemon = True
#     audio_thread.start()

@app.teardown_appcontext # Stop chuck when the flask app is closed
def teardown_appcontext(exception):
    if chuck_process != None:
        print("why would i be here")
        stop_chuck()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/start_hapticize', methods=['POST'])
def start_hapticize():
    global hapticizing, audio_thread
    hapticizing = True
    print("chuck process", chuck_process)
    if chuck_process != None:
        print("chuck started")
    else:
        print("CHUCK NOT STARTED")

    return jsonify({'status': 'Hapticizing started'})  # Just sets the flag
    
    return jsonify({'status': 'Hapticizing started'})

@app.route('/stop_hapticize', methods=['POST'])
def stop_hapticize():
    global hapticizing
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
        intensity = data.get('intensity')
        pitch = data.get('pitch')
        time_window = data.get('timeWindow')
        duration = data.get('duration')
        waveform_shape = data.get('waveformShape')

        # ... (Use the extracted parameters to control your haptic feedback)

        # Example: Print the received parameters to the console
        print("Received modulation parameters:")
        print(f"Intensity: {intensity}")
        print(f"Pitch: {pitch}")
        print(f"Time Window: {time_window}")
        print(f"Duration: {duration}")
        print(f"Waveform Shape: {waveform_shape}")

        # Example: Send OSC messages to Chuck (replace with your actual logic)
        client.send_message("/intensity", intensity)  # Assuming /intensity is the correct address
        client.send_message("/pitch", pitch)        # Assuming /pitch is the correct address
        # ... send other OSC messages

        return jsonify({'status': 'Modulation parameters received'}), 200  # Return a success response

    except Exception as e:
        print(f"Error processing modulation parameters: {e}")
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
        print(f"Error in /vibrate route: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500
    

    




def detect_and_send_pitch(audio, sample_rate):
    # pr = cProfile.Profile()  # Create a profiler object
    # pr.enable()
    # Convert audio to a Parselmouth Sound object
    sound = parselmouth.Sound(audio, sampling_frequency=sample_rate)
    rms = sound.get_rms()
    intensity = sound.get_intensity()
    #print("Intensity", sound.get_intensity())

        # Sound intensity threshold: if sound is less than 30 dB, ignore it
        # Probably needs to be higher than 30 in practice especially in a noisy environment
        # if intensity < 30:
        #     return
    #print("detect and send pitch")
    # Extract pitch using Parselmouth
    pitch = sound.to_pitch(pitch_floor=120)
    #print("FRAME LENGTH", pitch.dt)
    #print("whole thing length", pitch.get_total_duration())
    pitch_values = pitch.selected_array['frequency']

    total = 0.0
    valid = 0

    for value in pitch_values:
        # Detect pitches in human voice range: 80-300 Hz
        if value != 0:
            total = total + value
            valid += 1
    if valid > 0:
        value = total / valid
    else:
        value = 0
    
    value = total / len(pitch_values)
    #print("VALUE", value)

    vmin = 80
    vmax = 400
    if value > vmin and value < vmax:
        #print(value)

        # Normalize to haptic range: 100-300 Hz (SUBJECT TO CHANGE)
        hmin = 100
        hmax = 300
        normalized_pitch = hmin + ((value - vmin) / (vmax - vmin)) * hmax
        client.send_message("/pitch", normalized_pitch)
        # Normalize intensity to Chuck's gain range, 0-1
        # Guesstimating intensity range to be like 30-100 dB

    if intensity > 20:
        normalized_intensity = (intensity - 30) / (100 - 30)
        client.send_message("/loudness", normalized_intensity)
        # if intensity < 50:
        #     client.send_message("/loudness", 0.1)
        # elif intensity > 70:
        #     client.send_message("/loudness", 1.0)
        # else:
        #     client.send_message("/loudness", 0.5)
        #time.sleep(0.2)

    # pr.disable()  # Stop profiling
    # pr.print_stats(sort='time')

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
        return
    
    mono_audio = np.mean(indata, axis=1)
    detect_and_send_pitch(mono_audio, fs)

def audio_thread_function():
    duration = int(fs * 0.25)

    with sd.InputStream(channels=1, samplerate=fs, blocksize=duration, callback=audio_callback) as stream:
        print("Listening (audio thread)...")
        while True:
            time.sleep(0.001)



print(threading.enumerate())
print("stream closed? idk girl")
audio_thread_function()

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False, profile=False)