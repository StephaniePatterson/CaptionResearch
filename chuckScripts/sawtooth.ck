// Set up oscillator structure
SawOsc s => Gain g => WvOut wavOut => dac;  

"output.wav" => wavOut.wavFilename; // file to store output

// Initialize oscrecv object
OscRecv recv;
6449 => recv.port;
recv.listen();

// Osc message listener
OscIn oin;
OscMsg msg;
oin.listenAll();

// Event to receive modulation parameters (not currently using)
OscEvent config_event;
recv.event("/modulation/bundle, f, f, i, i, s") @=> config_event;

// Initialize parameters
float intensityFactor;
float pitchFactor;
int window;
int duration;
string shape;
<<< "Hello" >>>;

// Initialize OscEvents to receive pitch and loudness
OscEvent pitch_event;
OscEvent loudness_event;
recv.event("/pitch, f") @=> pitch_event;
recv.event("/loudness, f") @=> loudness_event;
1::second => dur timeout;
now => time lastMessage;
<<< "Ready" >>>;

now => time lastConfigCheck;
now => time lastPitchCheck;
now => time lastLoudnessCheck;
10::ms => dur checkrate;

spork ~ watchsilence(); // Start watchsilence func
//spork ~ watchloudness(); // Start watchloudness func

// Main loop: wait for pitch events and then update output wave
while (true) {
    pitch_event => now;
    loudness_event => now;
    while (pitch_event.nextMsg() && loudness_event.nextMsg()) {
        now => lastMessage;
        pitch_event.getFloat() => float newpitch;
        loudness_event.getFloat() => float newgain;
        //ADD THRESHOLD THING HERE
        //if (newpitch - s.freq > 10) {
        //    <<< "Threshold", newpitch >>>;
        //    newpitch => s.freq;
        //}
        <<< "Received pitch:", newpitch, "at time", now >>>;
        <<< "Received gain:", newgain >>>;
        newgain => g.gain;
        newpitch => s.freq;
        
        //s => g => wavOut => dac;
        //duration::ms => now;
    }
}


wavOut.closeFile();

// Function to wait for loudness events
fun void watchloudness() {
    while (true) {
        loudness_event => now;
        while (loudness_event.nextMsg()) {
            now => lastMessage;
            loudness_event.getFloat() => float newgain;
            <<< "Received gain:", newgain >>>;
            //newgain => g.gain;
            duration::ms => now;
        }
    }

}

//Function that silences sound when no signal has been received
fun void watchsilence() {
    while (true) {
        timeout => now;
        if (now - lastMessage >= timeout) {
            0 => g.gain;
        }
    }
}