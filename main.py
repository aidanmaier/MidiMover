import asyncio
from dev.playback import DataLoader
from midi import MidiOut
from mapping import note_map, pitchwheel_map

# Motion data variables
input_directory = './data/'
input_filename = 'rotation_z.csv'

# MIDI variables
midi_port = 'IAC Driver Bus 1'
midi_channel = 0
midi_notes = [i for i in range(128)]


# TEST CODE:

async def main():

    # Load data from .csv
    data = DataLoader(input_directory, input_filename)
    sample_rate = data.sample_rate
    sample_period = data.sample_period

    # Mapping variables
    input_range = [-1.0, 1.0]
    # note_range = [48, 84]

    # Stream sensor data and output as MIDI notes
    midi_out = MidiOut(midi_port, channel=midi_channel)

    # Callback function for stream
    def pitch_mod(sample):
        # Streaming rotation around z axis
        sensor = 'rotation_vector'
        axis = 'z'
        z_value = float(sample[(sensor, axis)]) 
        mod = pitchwheel_map(z_value, input_range)
        # midi_out.pitchMod(mod)
        print(f'z_rotation={z_value} -> pitchwheel={mod}') 

    print(f'\nSample rate: {sample_rate} Hz')
    print(f'Sample period: {sample_period} seconds\n')

    # Sustained note
    midi_out.noteOn(pitch=60)

    await data.stream(pitch_mod, loop=False)

    midi_out.noteOff(pitch=60)

if __name__ == '__main__':
    asyncio.run(main())


