SinOsc s;
200 => s.freq;
1.0 => s.gain;
s => dac;
<<< "Playing sine wave" >>>;
2::second => now;

PulseOsc p;
200 => p.freq;
1.0 => p.gain;
p => dac;
<<< "Playing pulse wave" >>>;
2::second => now;

SqrOsc q;
200 => q.freq;
1.0 => q.gain;
q => dac;
<<< "Playing square wave" >>>;
2::second => now;

TriOsc t;
200 => t.freq;
1.0 => t.gain;
t => dac;
<<< "Playing triangle wave" >>>;
2::second => now;

SawOsc w;
200 => w.freq;
1.0 => w.gain;
w => dac;
<<< "Playing sawtooth wave" >>>;
2::second => now;