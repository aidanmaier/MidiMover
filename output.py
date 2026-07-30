import mido
import asyncio
from typing import Any
from signal_processing import calculate_magnitude, quaternion_to_euler
from mapping import midi_map, pitchwheel_map

# Default MIDI CC controls
control_codes = {
            'Mod': 1, # mod wheel
            'Volume': 7,
            'Filt Res': 71, # filter resonance
            'Release': 72,
            'Attack': 73,
            'Filt Cut': 74, # filter cutoff
            'Portamento': 84,
            'Reverb': 91,
            'Tremolo': 92,
            'Chorus': 93,
            'Phaser': 95,
        }

output_mapping_functions = {
            'Note' : lambda x: x,
            'Bend' : pitchwheel_map,
            'Volume' : midi_map,
            'Filt Cut': midi_map,
            'Filt Res': midi_map,
        }

class MidiOut():
    """Wrapper for Mido output functionality."""
    
    def __init__(self, settings, channel: int = 0) -> None:
        self.channel = channel

        # Pointers to global settings
        self.settings = settings

    def open_outport(self, port_name: str) -> None:
        self._outport = mido.open_output(port_name)  # type: ignore

    def close_outport(self) -> None:
        self._outport.close()
    
    def note_on(self, pitch: int) -> None:
        """
        Starts a sustained note at the given pitch with velocity=64
        Input values: pitch [0..127]
        """
        msg = mido.Message('note_on', channel=self.channel, note=pitch, velocity=64)
        self._outport.send(msg)

    def note_off(self, pitch: int) -> None:
        """
        Ends the note at the given pitch
        Input values: pitch [0..127]
        """
        msg = mido.Message('note_off', channel=self.channel, note=pitch, velocity=0)
        self._outport.send(msg)
        
    def pitch_bend(self, mod: int, ) -> None:
        """
        Continuous pitch modification via pitchwheel message
        Input values: mod [-8192..8191]
        """
        msg = mido.Message('pitchwheel', channel=self.channel, pitch=mod)
        self._outport.send(msg)

    async def perc(self, pitch: int, duration: float = 0.1) -> None:
        """
        Play asyncronous time-limited note at the given pitch
        MIDI Note On message with auto Note Off message after awaiting duration
        Input values: 
            pitch (semitones) [0..127], 
            velocity [0..127], 
            duration (seconds) [any float]
        """
        self.note_on(pitch=pitch)
        await asyncio.sleep(duration)
        self.note_off(pitch=pitch)
    
    def cc(self, control: str, value: int) -> None:
        """
        MIDI Control Change message
        Input values: 
            control [valid controls held in midi.control_codes], 
            value [0..127]
        """
        outport = self._outport
        channel = self.channel
        control_code = control_codes[control]
        cc = mido.Message('control_change', channel=channel, control=control_code, value=value )
        outport.send(cc)

class MidiPlayer:
    def __init__(self, settings, midi_out: MidiOut) -> None:

        # Pointers to global settings
        self.settings = settings
        self.midi_out = midi_out

    def play(self, sample: dict[str, Any]) -> None:

        # Raw input data
        acceleration: list[float] = sample['sensors']['linear_acceleration']
        rotation: list[float] = sample['sensors']['rotation_vector']

        # Processed input parameters
        pitch, roll, yaw = rotation[:3]
        speed = calculate_magnitude(acceleration)

        input_values = {
            "Speed" : speed,
            "Yaw" : yaw,
            "Pitch" : pitch,
            "Roll" : roll,
        }

        # Map input and output parameters according to loaded patch
        patch_parameters = self.settings.loaded_patch_parameters_data

        mapped_vals = {}

        # Iterate through patch parameters
        for param_id, config in patch_parameters.items():
            input_name = config.get("input", None)
            output_name = config.get("output", None)
            in_range = config.get("input_range", [])
            out_range = config.get("output_range", [])

            # Skip unused parameters
            if not input_name or not output_name or len(in_range) < 2 or len(out_range) < 2:
                continue

            # Write mapped input_value to mapped_vals
            sensor_value = input_values.get(input_name)
            mapping_func = output_mapping_functions[output_name]
            if sensor_value is not None:
                output_value = mapping_func(
                    sensor_value,
                    in_range
                )
                mapped_vals[output_name] = output_value

        # Send MIDI data
        output_params = mapped_vals.keys()
        if 'Note' in output_params:
            pass # TODO: implement note control
        if 'Bend' in output_params:
            self.midi_out.pitch_bend(mapped_vals['Bend'])
        if 'Volume' in output_params:
            self.midi_out.cc('Volume', value=mapped_vals['Volume'])
        if 'Filt Cut' in output_params:
            self.midi_out.cc('Filt Cut', value=mapped_vals['Filt Cut'])
        if 'Filt Res' in output_params:
            self.midi_out.cc('Filt Res', value=mapped_vals['Filt Res'])

        print(mapped_vals) # DEBUG
