import mido
import asyncio
import queue
import numpy as np
import tkinter as tk
from typing import Any
from settings import Settings, SCALE_PATTERNS
from signal_processing import calculate_magnitude

class Scale():
    def __init__(self, root: int, scale_type: str) -> None:
        """
        Holds MIDI note values for a given musical scale type and root note.
        Input values:
            root [0..11] (C..B),
            scale_type [valid scale types held in SCALE_PATTERNS]
        """
        
        self.root = root
        self.type = scale_type
        self.pattern = SCALE_PATTERNS[scale_type] # degrees of the chromatic scale (1 octave)
        self.steps = len(self.pattern) # number of degrees per octave

        # Transpose scale to start on root and order by asc = lowest octave of scale
        self.octave = sorted([(note + root) % 12 for note in self.pattern])
        
        # All scale notes falling within MIDI [0..127] range
        full_scale = [note for note in self.octave]
        for octave in range(1, 11):
            for note in self.octave:
                new_note = note + (12 * octave)
                if new_note < 128:
                    full_scale.append(new_note)
        self.full = full_scale

def midi_map(value: float, input_range: list[float], output_range: list[int] = [0, 127]) -> int:
    """
    Maps continuous sensor data to discreet midi values with settable input range to output range.
    Parameters: 
    input_range [floor, ceiling]
    output_range [floor, ceiling]: in midi range [0..127]
    """

    output_floor = output_range[0]
    output_ceiling = output_range[1]

    mapped_value = np.interp(value, input_range, output_range) # interpolate value from input to output ranges
    limited_value = max(output_floor, min(output_ceiling, mapped_value)) # hard limit output to output range

    return int(limited_value)

class MidiOut():
    """Wrapper for Mido output functionality."""
    
    def __init__(self, settings: Settings, channel: int = 0) -> None:
        self.channel = channel

        # Pointers to global settings
        self.settings = settings
        self.control_codes = settings.control_codes

    def open_outport(self, port_name: str) -> None:
        self._outport = mido.open_output(port_name)  # type: ignore

    def close_outport(self) -> None:
        self._outport.close()

    def is_open(self) -> bool:
        """Returns True if outport exists and is open."""
        return self._outport is not None and not getattr(self._outport, 'closed', True)

    def _safe_send(self, msg: mido.Message) -> None:
        """Guards against sending to closed ports."""
        if not self.is_open():
            return

        try:
            self._outport.send(msg)  # type: ignore
        except (ValueError, RuntimeError) as e:
            print(f"MidiOut Warning: Cannot send message. Port closed or invalid ({e}).")
    
    def note_on(self, pitch: int) -> None:
        """
        Starts a sustained note at the given pitch with velocity=64
        Input values: pitch [0..127]
        """
        msg = mido.Message('note_on', channel=self.channel, note=pitch, velocity=64)
        self._safe_send(msg)

    def note_off(self, pitch: int) -> None:
        """
        Ends the note at the given pitch
        Input values: pitch [0..127]
        """
        msg = mido.Message('note_off', channel=self.channel, note=pitch, velocity=0)
        self._safe_send(msg)
        
    def pitch_bend(self, mod: int, ) -> None:
        """
        Continuous pitch modification via pitchwheel message
        Input values: mod [-8192..8191]
        """
        msg = mido.Message('pitchwheel', channel=self.channel, pitch=mod)
        self._safe_send(msg)

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
            control [valid controls held in midi.CONTROL_CODES], 
            value [0..127]
        """
        channel = self.channel
        control_code = self.control_codes[control]
        cc = mido.Message('control_change', channel=channel, control=control_code, value=value )
        self._safe_send(cc)


class MidiPlayer:
    def __init__(self, settings: Settings, midi_out: MidiOut) -> None:

        # Pointers to global settings
        self.settings = settings
        self.midi_out = midi_out
        self.active_scale: tk.StringVar = self.settings.active_scale
        self.active_root_note: tk.IntVar = self.settings.active_root_note

        # Track midi note_value [0..127]
        self.previous_note = tk.IntVar(value=0)

        # Thread-safe queue for buffering MIDI outputs across threads
        self.midi_queue = queue.Queue()

        # Local active scale object
        self.active_scale_object = Scale(self.active_root_note.get(), self.active_scale.get())

        # Manage active scale object changes
        self.settings.active_scale.trace_add('write', self._update_active_scale_object)
        self.settings.active_root_note.trace_add('write', self._update_active_scale_object)
        self.settings.active_root_name.trace_add('write', self._update_active_scale_object)
        

    def play(self, sample: dict[str, Any]) -> None:
        """Processes sensor data samples and sends them to the thread-safe queue."""

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
            'Width': None, 
            'Height': None, 
            'Depth': None,
        }

        # Map input and output parameters according to loaded patch
        patch_parameters = self.settings.loaded_patch_parameters_data

        mapped_vals: dict[str, int] = {}

        # Iterate through patch parameters to extract in/out mappings
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
            if sensor_value is not None:
                output_value = midi_map(
                    sensor_value,
                    in_range,
                    out_range
                )
                mapped_vals[output_name] = output_value

            # TODO: test note filter

            # If Note parameter
            if 'Note' in mapped_vals:
                # filter for note same as previous note
                if mapped_vals['Note'] == self.previous_note.get():
                    mapped_vals.pop('Note')
                    continue
                # filter for note not in scale
                elif mapped_vals['Note'] not in self.active_scale_object.full:
                    mapped_vals.pop('Note')
                    continue
                else:
                    self.previous_note.set(mapped_vals['Note'])

        # Send mapped values to the thread-safe queue
        if mapped_vals:
            self.midi_queue.put(mapped_vals)

    async def process_queue(self) -> None:
        """
        Flushes queue and sends all queued MIDI messages.
        Runs on the async loop so note playback can be scheduled correctly.
        """
        while not self.midi_queue.empty():
            try:
                mapped_vals: dict[str, int] = self.midi_queue.get_nowait()

                for param, value in mapped_vals.items():
                    if param == 'Note':
                        # Schedule MIDI note playback without blocking the queue processor.
                        asyncio.create_task(self.midi_out.perc(value))
                    else:
                        # Send midi CC messages immediately.
                        self.midi_out.cc(param, value)

                print(mapped_vals)  # DEBUG

            except queue.Empty:
                break

    def _update_active_scale_object(self, *args):
        """Refreshes active scale object when scale or root note name changes."""
        scale_type = self.active_scale.get()
        root = self.active_root_note.get()
        self.active_scale_object = Scale(root, scale_type)

            
