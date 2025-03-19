OscRecv recv;
6449 => recv.port;
recv.listen();

OscEvent pitch_event;
OscEvent loudness_event;
recv.event("/pitch, f") @=> pitch_event;
recv.event("/loudness, f") @=> loudness_event;

SinOsc s => Gain g => WvOut wavOut => dac;
"output2.wav" => wavOut.wavFilename;

1::second => dur timeout;
now => time lastMessage;

spork ~ watchsilence();

while (true) {
    pitch_event => now;
    loudness_event => now;
    
    while (pitch_event.nextMsg() && loudness_event.nextMsg()) {
        now => lastMessage;
        
        float newpitch;
        float newgain;
        pitch_event.getFloat() => newpitch;
        loudness_event.getFloat() => newgain;
        
        <<< "Pitch:", newpitch, "Gain:", newgain >>>;

        // Emotional mapping logic: determine emotion type
        if (newpitch < 100) {
            // Low pitch -> sadness or calm
            newgain * 0.5 => g.gain;  // softer response than normal
            (100 / newpitch) * 50 => s.freq; // lower frequencies for calm emotions
        } else if (newpitch > 120) {
            // High pitch -> excitement, fear
            newgain * 1.5 => g.gain;  // stronger response than normal
            (200 / newpitch) * 250 => s.freq; // higher frequencies for excitement
        } else {
            // Mid pitch -> neutral, stable emotion
            newgain => g.gain;  // normal response
            newpitch => s.freq;  // direct mapping to frequency
        }

        
    }
}

wavOut.closeFile();

fun void watchsilence() {
    while (true) {
        timeout => now;
        if (now - lastMessage >= timeout) {
            0 => g.gain;
        }
    }
}

