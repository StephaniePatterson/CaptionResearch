SinOsc s => Gain g => WvOut wavOut => dac;  
"output.wav" => wavOut.wavFilename;
OscRecv recv;
6449 => recv.port;
recv.listen();

OscIn oin;
OscMsg msg;
oin.listenAll();

OscEvent config_event;
recv.event("/modulation/bundle, f, f, i, i, s") @=> config_event;

float intensityFactor;
float pitchFactor;
int window;
int duration;
string shape;
<<< "Hello" >>>;

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

spork ~ watchsilence();

while (true) {
    pitch_event => now;
    loudness_event => now;
    while (pitch_event.nextMsg() && loudness_event.nextMsg()) {
        now => lastMessage;
        pitch_event.getFloat() => float newpitch;
        loudness_event.getFloat() => float newgain;
        //ADD THRESHOLD THING HERE
        <<< "Received pitch:", newpitch, "at time", now >>>;
        <<< "Received gain:", newgain >>>;
        newpitch => s.freq;
        newgain => g.gain;
        //s => g => wavOut => dac;
        duration::ms => now;
    }
}




wavOut.closeFile();

//Function that silences sound when no signal has been received
fun void watchsilence() {
    while (true) {
        timeout => now;
        if (now - lastMessage >= timeout) {
            0 => g.gain;
        }
    }
}