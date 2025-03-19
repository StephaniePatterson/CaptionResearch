//code that should receive modulation bundle, if i need that

while (true) {
    oin => now;

    while (oin.recv(msg)) {
        if (msg.address == "modulation/bundle") {
            <<< "hi" >>>;
        }
    }
    
    <<< msg >>>;
    <<< "here" >>>;
    if (msg.address == "modulation/bundle, f, f, i, i, s") {
        <<< "heyy" >>>;
    }
    if(now - lastConfigCheck >= checkrate){
        now => lastConfigCheck;
        if (config_event.nextMsg()) {
            config_event.getFloat() => intensityFactor;
            config_event.getFloat() => pitchFactor;
            config_event.getInt() => window;
            config_event.getInt() => duration;
            config_event.getString() => shape;

            <<< "Received" >>>;
            <<< "Config event received" >>>;
        }
    }
    if(now - lastPitchCheck >= checkrate){
        now => lastPitchCheck;
        while (pitch_event.nextMsg() && loudness_event.nextMsg()) {
            now => lastMessage;
            pitch_event.getFloat() => float newpitch;
            loudness_event.getFloat() => float newgain;
            <<< "Received pitch:", newpitch, "at time", now >>>;
            <<< "Received gain:", newgain, "at time", now >>>;
            newpitch * pitchFactor => s.freq;
            newgain * intensityFactor => g.gain;
            //s => g => wavOut => dac;
            //1::second => now;
        }
    }
}