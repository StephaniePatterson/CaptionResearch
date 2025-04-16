SinOsc s;

fun void startWave() {
    s => dac;
    2::second => now;
}

fun void changePitch(float newpitch) {
    newpitch => s.freq;
}

fun void changeGain(float newgain) {
    newgain => s.gain;
}

fun void changeWave(string newwave) {
    if (newwave = "Sine") {
        SinOsc s;
    }
    if (newwave = "Sawtooth") {
        SawOsc s;
    }
    if (newwave = "Pulse") {
        PulseOsc s;
    }

}