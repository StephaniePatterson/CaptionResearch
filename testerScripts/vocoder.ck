// Audio Input
adc => Gain gain => blackhole;
gain.gain(1.0);

// Carrier Signal
SinOsc carrier => Gain carrierGain => dac;
carrierGain.gain(0.0); // Initially muted
440 => carrier.freq; // Carrier frequency (adjust as needed)

// Buffer and RMS Calculation
128 => int bufferSize; // Adjust buffer size as needed
float buffer[bufferSize];
0 => int bufferIndex;

while (true)
{
    gain.last() => buffer[bufferIndex];
    bufferIndex++;

    if (bufferIndex >= bufferSize)
    {
        0 => bufferIndex;

        // Calculate RMS
        0.0 => float sum;
        for (0 => int i; bufferSize > i; i++)
        {
            buffer[i] * buffer[i] => float squaredSample;
            sum + squaredSample => sum;
        }
        sum / bufferSize => float meanSquared;
        Math.sqrt(meanSquared) => float rms;

        // Scale RMS (Normalize and map to 0-255)
        //simple normalization.
        0.0 => float max;
        for(0 => int i; bufferSize > i; i++){
            Math.abs(buffer[i]) => float absValue;
            if (absValue > max){
                absValue => max;
            }
        }
        if(max > 0){
            rms / max => rms;
        }

        rms => carrierGain.gain;
    }
    1::samp => now; // Process one sample at a time
}