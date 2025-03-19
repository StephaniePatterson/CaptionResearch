import sounddevice as sd
import numpy as np
import time

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    audio_buffer = indata[:, 0]  # Get mono audio data
    rms = np.sqrt(np.mean(audio_buffer**2)) # Fast RMS calculation
    scaled_rms = int(np.interp(rms, (0, 1), (0, 255))) #scale values.
    print(scaled_rms)
    #send scaled_rms value to haptic device here.
    # example: ser.write(bytes([scaled_rms]))

try:
    with sd.InputStream(callback=audio_callback):
        print("Listening... Press Ctrl+C to stop.")
        while True:
            time.sleep(0.1)
except KeyboardInterrupt:
    print("\nStopped.")