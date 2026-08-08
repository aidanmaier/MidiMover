import mido
import asyncio
import queue
import numpy as np
import tkinter as tk
from typing import Any
from settings import Settings, SCALE_PATTERNS, NOTE_NAMES
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

def midi_to_signed_pitch(midi_val: int) -> str:
    """Converts a numerical MIDI value to its note pitch with numerical octave."""
    pitch = NOTE_NAMES[midi_val % 12]
    octave = midi_val // 12
    return f'{pitch}{octave}'

def midi_map(
        value: float, 
        input_range: tuple[float, float], 
        output_range: tuple[int, int] = (0, 127),
        invert: bool = False,
        exponential: bool = False
) -> int:
    """
    Maps continuous sensor data to discreet midi values from settable input range to output range.
    Parameters: 
    input_range [floor, ceiling]
    output_range [floor, ceiling]: in midi range [0..127]
    invert: flips the mapping
    exponential: changes mapping curve from linear to exponential
    """
    in_min, in_max = input_range[0], input_range[1]
    out_min, out_max = output_range[0], output_range[1]

    # Normalize input to [0.0, 1.0]
    if in_max == in_min:
        norm = 0.0
    else:
        norm = (value - in_min) / (in_max - in_min)
    norm = max(0.0, min(1.0, norm))

    # Invert mapping curve
    if invert:
        norm = 1.0 - norm

    # Exponential mapping
    if exponential:
        norm = norm ** 2

    # Scale to MIDI output range [0, 127]
    mapped = out_min + norm * (out_max - out_min)

    return int(round(np.clip(mapped, 0, 127)))

def snap_to_scale(pitch: int, valid_notes: list[int]) -> int:
    """Finds the closest note in the active scale to the given MIDI pitch."""
    if not valid_notes:
        return pitch
    return min(valid_notes, key=lambda note: abs(note - pitch))

class MidiOut():
    """Wrapper for Mido output functionality."""
    
    def __init__(self, settings: Settings) -> None:
        self.channel = settings.active_midi_channel.get()
        self._outport: mido.ports.BaseOutput | None = None

        # Pointers to global settings
        self.settings = settings
        self.control_codes = settings.control_codes
        self.active_midi_channel = settings.active_midi_channel
        self._port_lock = settings.midi_port_lock

        # Track MIDI channel changes
        self.active_midi_channel.trace_add('write', self._update_channel)

    def open_outport(self, port_name: str) -> None:
        """Opens new MIDI ouput port."""
        with self._port_lock: # guard thread port access
            self._outport = mido.open_output(port_name)  # type: ignore

    def close_outport(self) -> None:
        """Closes open MIDI output port if any."""
        with self._port_lock: # guard thread port access
            if self._outport is not None:
                self._outport.close()
                self._outport = None

    def _update_channel(self, *args) -> None:
            """Callback triggered when settings.active_midi_channel is modified."""
            try:
                new_channel = self.settings.active_midi_channel.get()

                # Guard for invalid entry
                if new_channel not in range(16):
                    raise ValueError('MIDI channel must be in the range [0, 15]')
                self.channel = new_channel

            except tk.TclError:
                # Handles temporary invalid/empty inputs in GUI entry widgets
                pass

    def is_open(self) -> bool:
        """Returns True if outport exists and is open."""
        outport = getattr(self, '_outport', None)
        return outport is not None and not getattr(self._outport, 'closed', True)

    def _safe_send(self, msg: mido.Message) -> None:
        """Guards against sending to closed ports."""
        with self._port_lock: # guard thread port access
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
        control_code = self.control_codes[control]
        cc = mido.Message('control_change', channel=self.channel, control=control_code, value=value )
        self._safe_send(cc)

    def all_notes_off(self) -> None:
        """Kills all notes."""
        for pitch in range(128):
            self.note_off(pitch)

    def reset_param(self, param_name: str, active_note: int | None = None) -> None:
        """Resets a specific output parameter to its default baseline state."""
        if param_name == 'Note':
            if active_note is not None:
                self.note_off(active_note)
            # self.all_notes_off()
        elif param_name in self.control_codes:
            # Default to neutral mid position
            default_val = 64
            self.cc(param_name, default_val)

    def reset_all(self) -> None:
        """Kills all notes and resets used controls to mid point."""
        with self._port_lock: # guard thread port access
            if not self.is_open():
                return

            self.all_notes_off()

            # Reset standard CC channels to neutral mid position
            for param_name in self.control_codes.keys():
                self.reset_param(param_name, active_note=None)


class MidiPlayer:
    def __init__(self, settings: Settings, midi_out: MidiOut) -> None:

        # Pointers to global settings
        self.settings = settings
        self.midi_out = midi_out
        self.active_scale: tk.StringVar = self.settings.active_scale
        self.active_root_note: tk.IntVar = self.settings.active_root_note

        # Track midi note_value [0..127]
        self.previous_note = tk.IntVar(value=0)

        # Thread-safe send queue for buffering MIDI outputs across threads
        self.midi_queue = queue.Queue()

        # Local active scale object
        self.active_scale_object = Scale(self.active_root_note.get(), self.active_scale.get())

        # Manage active scale object changes
        self.settings.active_scale.trace_add('write', self._update_active_scale_object)
        self.settings.active_root_note.trace_add('write', self._update_active_scale_object)
        self.settings.active_root_name.trace_add('write', self._update_active_scale_object)
        
    def play(self, sample: dict[str, Any]) -> None:
        """Processes sensor data samples and sends them to the thread-safe queue."""

        # Raw sensor data
        acceleration: list[float] = sample['sensors']['linear_acceleration']
        rotation: list[float] = sample['sensors']['rotation_vector']

        # Guard for missing values
        if len(rotation) < 3 or not acceleration:
            return 

        # Processed input parameters
        pitch, roll, yaw = rotation[:3]
        speed = calculate_magnitude(acceleration)

        input_values = {
            "Speed" : speed,
            "Turn" : yaw,
            "Tilt" : pitch,
            "Twist" : roll, 
        }

        # Map input and output parameters according to loaded patch
        patch_parameters = self.settings.loaded_patch_parameters_data
        mapped_vals: dict[str, int | None] = {}

        # Iterate through patch parameters to extract in/out mappings
        for param_id, config in patch_parameters.items():
            input_name = config.get("input")
            output_name = config.get("output")
            in_range = config.get("input_range", [])
            out_range = config.get("output_range", [])
            invert = config.get("invert", False)
            exponential = config.get("exponential", False)

            # Skip unused or incomplete parameters
            if not input_name or not output_name or len(in_range) < 2 or len(out_range) < 2:
                continue

            # Write mapped input_value to mapped_vals
            sensor_value = input_values.get(input_name)            
            if sensor_value is not None:
                output_value = midi_map(
                    sensor_value,
                    in_range,
                    out_range,
                    invert,
                    exponential
                )
                mapped_vals[output_name] = output_value

        # Note quantization and filter repeated notes
        if 'Note' in mapped_vals and mapped_vals['Note'] is not None:
            raw_pitch = mapped_vals['Note']

            # Quantize pitch to nearest note in scale
            quantized_pitch = snap_to_scale(raw_pitch, self.active_scale_object.full)

            # Trigger only if different from previous note
            if quantized_pitch == self.previous_note.get():
                mapped_vals['Note'] = None
            else:
                mapped_vals['Note'] = quantized_pitch
                self.previous_note.set(quantized_pitch)

        # Send mapped values to the thread-safe queue
        if mapped_vals:
            self.midi_queue.put(mapped_vals)

    async def process_queue(self) -> None:
        """
        Sends all queued MIDI messages and clears send queue.
        Runs on the async loop so note playback can be scheduled correctly.
        """
        while not self.midi_queue.empty():
            try:
                mapped_vals: dict[str, Any] = self.midi_queue.get_nowait()

                # Handle internal parameter reset commands
                if '_RESET_' in mapped_vals:
                    reset_param = mapped_vals['_RESET_']
                    last_note = mapped_vals.get('_VALUE_')
                    self.midi_out.reset_param(reset_param, last_note)
                    continue

                for param, value in mapped_vals.items():
                    if value:
                        if param == 'Note':
                            # Schedule MIDI note playback without blocking the queue processor.
                            asyncio.create_task(self.midi_out.perc(value))
                        else:
                            # Send midi CC messages immediately.
                            self.midi_out.cc(param, value)

                print(mapped_vals) #DEBUG
                            
            except queue.Empty:
                break

    def _update_active_scale_object(self, *args):
        """Refreshes active scale object when scale or root note name changes."""
        scale_type = self.active_scale.get()
        root = self.active_root_note.get()
        self.active_scale_object = Scale(root, scale_type)
        # Update global setting
        self.settings.active_scale_full = self.active_scale_object.full

    def reset_parameter(self, param_name: str) -> None:
        """Queue a thread-safe reset command to reset a specific MIDI parameter."""
        if param_name == 'Note':
            last_note = self.previous_note.get()
            self.previous_note.set(0)
            self.midi_queue.put({'_RESET_': 'Note', '_VALUE_': last_note})
        else:
            self.midi_queue.put({'_RESET_': param_name})

    def reset_all(self) -> None:
        """Clears the pending MIDI queue and triggers immediate MIDI hardware reset."""
        # Clear MIDI send queue
        while not self.midi_queue.empty():
            try:
                self.midi_queue.get_nowait()
            except queue.Empty:
                break

        # Clear tracked pitch
        self.previous_note.set(0)

        # Send hardware reset
        self.midi_out.reset_all()

            
