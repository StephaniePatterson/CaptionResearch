const intensitySlider = document.getElementById('intensity');
const intensityScale = document.getElementById('intensityScale');
const pitchSlider = document.getElementById('pitch');
const pitchScale = document.getElementById('pitchScale');
const timeWindowInput = document.getElementById('timeWindow');
const timeWindowVal = document.getElementById('timeWindowVal');
const waveformShapeSelect = document.getElementById('waveformShape');
const vibrateButton = document.getElementById('vibrateButton');
const stopButton = document.getElementById('stopButton');
const hapticizeButton = document.getElementById('hapticizeButton');
const stopHapticizeButton = document.getElementById('stopHapticizeButton');
const chuckButton = document.getElementById('chuckButton');
const stopChuckButton = document.getElementById('stopChuckButton');
const statusDiv = document.getElementById('status');
const sendPitchCheckbox = document.getElementById('sendPitch');
const sendVolumeCheckbox = document.getElementById('sendVolume');

let hapticizing = false; // Flag to track hapticizing state

// Function to send modulation parameters to the backend
function sendModulationParams() {
    const intensity = intensitySlider.value;
    const pitch = pitchSlider.value;
    const timeWindow = timeWindowInput.value;
    const waveformShape = waveformShapeSelect.value;
    const sendPitch = sendPitchCheckbox.checked;
    const sendVolume = sendVolumeCheckbox.checked;

    fetch('/modulation', { // New route for modulation parameters
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            intensity: intensity,
            pitch: pitch,
            timeWindow: timeWindow,
            waveformShape: waveformShape,
            sendPitch: sendPitch,
            sendVolume: sendVolume
        })
    })
    .then(response => response.json())
    .then(data => {
                console.log("Modulation parameters sent:", data);
    })
    .catch(error => {
        console.error("Error sending modulation parameters:", error);
    });
}


// Event listeners for real-time adjustments
intensitySlider.addEventListener('input', () => {
    intensityScale.textContent = intensitySlider.value;
    sendModulationParams(); // Send parameters immediately
});

pitchSlider.addEventListener('input', () => {
    pitchScale.textContent = pitchSlider.value;
    sendModulationParams(); // Send parameters immediately
});

timeWindowInput.addEventListener('input', () => {
    timeWindowVal.textContent = timeWindowInput.value;
    sendModulationParams(); // Send parameters immediately
});

waveformShapeSelect.addEventListener('change', () => {
    waveformShape = waveformShapeSelect.value;
    sendModulationParams();
});

sendPitchCheckbox.addEventListener('change', () => {
    sendPitch = sendPitchCheckbox.checked;
    sendModulationParams();
});

sendVolumeCheckbox.addEventListener('change', () => {
    sendVolume = sendVolumeCheckbox.checked;
    sendModulationParams();
});


vibrateButton.addEventListener('click', () => {
    // One-time vibration command
    fetch('/vibrate', {
        method: 'POST',
        // ... (rest of the fetch request)
    });
});

stopButton.addEventListener('click', () => {
    // ... (stop logic)
});

hapticizeButton.addEventListener('click', () => {
  hapticizing = true;
  hapticizeButton.disabled = true;
  stopHapticizeButton.disabled = false;
  sendModulationParams(); // Send initial parameters
    fetch('/start_hapticize', { // New route to start hapticizing
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        statusDiv.textContent = data.status;
    })
    .catch(error => {
        console.error("Error starting hapticizing:", error);
        statusDiv.textContent = error;
        hapticizing = false; // Reset flag in case of error
        hapticizeButton.disabled = false;
        stopHapticizeButton.disabled = true;
    });
});

stopHapticizeButton.addEventListener('click', () => {
    hapticizing = false;
    hapticizeButton.disabled = false;
    stopHapticizeButton.disabled = true;
      fetch('/stop_hapticize', { // New route to stop hapticizing
          method: 'POST'
      })
      .then(response => response.json())
      .then(data => {
          statusDiv.textContent = data.status;
      })
      .catch(error => {
          console.error("Error stopping hapticizing:", error);
          statusDiv.textContent = "Error stopping.";
      });
  });

  chuckButton.addEventListener('click', () => {
    fetch('/start_chuck', {
        method: 'POST'
    })
  })