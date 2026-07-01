import time
from playback import DataLoader
from midi import MidiOut
from mapping import midi_map

# Motion data variables
input_directory = './data/'
input_filename = 'gesture.csv'

# MIDI variables
midi_port = 'IAC Driver Bus 1'
midi_channel = 0
midi_notes = [i for i in range(128)]

# Load data from .csv
gyro_streamer = DataLoader(input_directory, input_filename)
polling_rate = gyro_streamer.polling_rate

print(f'\nPolling rate: {polling_rate} Hz\n')

# Stream values for given sensor and axis at the polling rate
gyro_x = gyro_streamer.stream('gyroscope', 'x')
gyro_y = gyro_streamer.stream('gyroscope', 'y')
gyro_z = gyro_streamer.stream('gyroscope', 'z')

# Stream sensor data and output as MIDI notes
midi_out = MidiOut(midi_port, chan=midi_channel)

input_range = [-7.6, 8.4]
midi_range = [48, 84]

loop = True

while True:
    for sample in gyro_y:
        note = midi_map(sample, input_range, midi_range)
        print(f"gyro_y={sample:.3f} -> midi_note={note}")
        midi_out.note(pitch=note, vel=64, dur=0.1)
        time.sleep(1/gyro_streamer.polling_rate) # convert Hz to seconds
    if not loop:
        break


