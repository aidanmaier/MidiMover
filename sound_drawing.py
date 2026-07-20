import asyncio
from capture import DataStreamer
from signal_processing import calculate_magnitude
from midi import MidiOut
from mapping import midi_map, pitchwheel_map

# Live data input vriables
ws_address = '_websocket._tcp.local.'
sensors = [
    # 'gyroscope', 
    # 'accelerometer', 
    'rotation_vector', 
    'linear_acceleration'
        ]
sample_rate = 50 # Hz

# MIDI ouput variables
midi_port = 'IAC Driver Bus 1'
midi_channel = 0

# Mapping variables
mag_range = [0.0, 15.0]
rot_range = [-1.0, 1.0]

static_pitch = 69

async def main():

    # Stream live data
    data = DataStreamer(ws_address, sensors)

    # Stream sensor data and output as MIDI notes
    midi_out = MidiOut(midi_port, channel=midi_channel)

    # Callback function
    def draw_sound(sample):
        # Motion parameters
        acc = sample['sensors']['linear_acceleration']
        rot = sample['sensors']['rotation_vector']
        rx, ry, rz = rot[:3]
        mag = calculate_magnitude(acc)

        # Midi parameters
        vol = midi_map(mag, mag_range)
        pitch = pitchwheel_map(rx, rot_range)
        filt = midi_map(ry, rot_range)

        # Midi Control messages
        midi_out.cc('volume', value=vol)
        # print(f'Magnitude: {mag}, CC Volume: {vol}')
        # midi_out.pitchMod(pitch)
        # print(f'Y-Rotation: {ry}, Pitchwheel: {pitch}')
        midi_out.cc('cutoff', value=filt)

    # Sustained note
    midi_out.noteOn(pitch=static_pitch)

    await data.stream(draw_sound, sample_rate)

    midi_out.noteOff(pitch=static_pitch)

if __name__ == '__main__':
    asyncio.run(main())


