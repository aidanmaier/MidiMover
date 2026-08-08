import tkinter as tk
import os
import json
from pathlib import Path
from threading import RLock


# Hardcoded backup defaults, immutable from within app
FACTORY_SETTINGS = {
    "ws_address" : "_websocket._tcp.local.",
    "sensors" : ["rotation_vector", "linear_acceleration"],
    "input_disconnected_label" : "< Connect Device >",
    "output_disconnected_label" : "< Connect MIDI Port >",
    "default_sample_rate" : 50,
    "default_patch" : "",
    "default_device" : "SensorServer._websocket._tcp.local.",
    "default_outport" : "IAC Driver Bus 1"
}

FACTORY_PATCHES = {
    "patches" : {
        "< new instrument >" : {
            "description": "A blank canvas.",
            "channel": 0,
            "root_note" : 2,
            "scale": "Major",
            "legato": False,
            "parameters": {
                "0": {
                    "exponential" : False,
                    "invert" : False,
                    "input": None,
                    "input_range": [],
                    "output": None,
                    "output_range": []
                },
                "1": {
                    "exponential" : False,
                    "invert" : False,
                    "input": None,
                    "input_range": [],
                    "output": None,
                    "output_range": []
                },
                "2": {
                    "exponential" : False,
                    "invert" : False,
                    "input": None,
                    "input_range": [],
                    "output": None,
                    "output_range": []
                },
                "3": {
                    "exponential" : False,
                    "invert" : False,
                    "input": None,
                    "input_range": [],
                    "output": None,
                    "output_range": []
                }
            }
        }
    }
}

# Map note number (list index) to note name (sharps only)
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B',]

# Octave patterns for a selection of common (12-tet) scales 
SCALE_PATTERNS = {
    'Chromatic': [i for i in range(11)],
    'Whole Tone': [i for i in range(0, 11, 2)],
    'Octatonic': [0, 2, 3, 5, 6, 8, 9, 11],
    'Major': [0, 2, 4, 5, 7, 9, 11],
    'Lydian': [0, 2, 4, 6, 7, 9, 11],
    'Mixolydian': [0, 2, 4, 5, 7, 9, 10],
    'Melodic Minor': [0, 2, 3, 5, 7, 9, 11],
    'Dorian': [0, 2, 3, 5, 7, 9, 10],
    'Natural Minor': [0, 2, 3, 5, 7, 8, 10],
    'Phrygian': [0, 1, 3, 5, 7, 8, 10],
    'Harmonic Minor': [0, 2, 3, 5, 7, 8, 11],
    'Major Pentatonic': [0, 2, 4, 7, 9],
    'Minor Pentatonic': [0, 3, 5, 7, 10],
    # 'Pelog': [],
    # 'Sorog': [],
}

# Default MIDI CC controls
CONTROL_CODES = {
    'Volume': 7, # master volume/output
    'Filt Res': 71, # filter resonance
    'Filt Cut': 74, # filter cutoff
    'Attack': 73, # volume envelope attack
    'Release': 72, # volume envelope release
    'User 1': 85, # custom user parameter 1
    'User 2': 86, # custom user parameter 2
    'User 3': 89, # custom user parameter 3
    'User 4': 90, # custom user parameter 4
}


class Settings:
    """Shared config for global settings."""
    # Settings object passed to all gui components so all variables are settable locally
    # tk variables refire when updated
    def __init__(self, settings_filepath: Path, patches_filepath: Path):

        # Constants
        self.settings_filepath = settings_filepath
        self.patches_filepath = patches_filepath
        self.note_names = NOTE_NAMES
        self.scale_patterns = SCALE_PATTERNS
        self.control_codes = CONTROL_CODES

        # Guards access to MidiOutput._outport across threads to avoid PyEval_RestoreThread GIL assertion bug
        self.midi_port_lock = RLock() # re-entrant lock can be acquired multiple times by the same thread

        self.saved_settings = self._load_settings()
        s = self.saved_settings

        self.saved_patches_data = self._load_patches()
        p = self.saved_patches_data

        # Immutable app settings
        self.input_parameter_types = [
            '', # blank parameter = no output
            'Speed', 
            'Tilt', 
            'Turn', 
            'Twist', 
            ]
        self.output_parameter_types = ['', 'Note'] + [p for p in CONTROL_CODES.keys()]

        self.ws_address: str = FACTORY_SETTINGS['ws_address']
        self.sensors: list[str] = FACTORY_SETTINGS['sensors']
        self.input_disconnected_label: str = FACTORY_SETTINGS['input_disconnected_label']
        self.output_disconnected_label: str = FACTORY_SETTINGS['output_disconnected_label']

        # User settings, load factory setting if missing
        self.default_sample_rate: int = s.get('default_sample_rate', FACTORY_SETTINGS['default_sample_rate'])
        self.default_midi_channel: int = 0 # TODO: wire into settings.json
        self.default_patch = tk.StringVar(value=s.get('default_patch', FACTORY_SETTINGS['default_patch']))
        self.default_device = tk.StringVar(value=s.get('default_device', FACTORY_SETTINGS['default_device']))
        self.default_outport = tk.StringVar(value=s.get('default_outport', FACTORY_SETTINGS['default_outport']))

        self.active_scale = tk.StringVar(value='Major Pentatonic')
        self.active_root_note = tk.IntVar(value=2) # root note number
        self.active_root_name = tk.StringVar(value=self.note_names[self.active_root_note.get()]) # root note letter
        self.active_scale_full = []

        self.saved_patches_list = list(p['patches'].keys())

        # Runtime variables
        self.sample_rate = tk.IntVar(value=self.default_sample_rate)
        self.connection_status = tk.StringVar(value='Unconnected')
        self.running_status = tk.BooleanVar(value=False)
        self.selected_input = tk.StringVar(value='')
        self.selected_output = tk.StringVar(value='')

        self.input_connection = tk.StringVar(value='')
        self.input_connection_name = tk.StringVar(value=self.input_disconnected_label)
        self.input_connection_status = tk.BooleanVar(value=False)

        self.output_connection = tk.StringVar(value='')
        self.output_connection_name = tk.StringVar(value=self.output_disconnected_label)
        self.output_connection_status = tk.BooleanVar(value=False)

        self.loaded_patch_name = tk.StringVar(value='')
        self.loaded_patch_description = tk.StringVar(value='')
        self.loaded_patch_parameters_data = {}

        self.active_midi_channel = tk.IntVar(value=self.default_midi_channel)

        # Write default changes to settings.json
        self.default_device.trace_add('write', self._write_default_device)
        self.default_outport.trace_add('write', self._write_default_outport)
        self.default_patch.trace_add('write', self._write_default_patch)

    def _save_settings(self, data: dict) -> None:
        """Writes settings to disk and saved_settings variable."""

        os.makedirs(os.path.dirname(self.settings_filepath), exist_ok=True)  # create directory if does not exist
        with open(self.settings_filepath, 'w') as OUTFILE:
            json.dump(data, OUTFILE, indent=4)

    def _load_settings(self) -> dict:
        """Loads settings from disk, creating a file from factory settings if missing."""
        # create directory and new settings file if missing
        if not os.path.exists(self.settings_filepath):
            self._save_settings(FACTORY_SETTINGS)
            return dict(FACTORY_SETTINGS)
        
        try:
            with open(self.settings_filepath, 'r') as INFILE:
                return json.load(INFILE)
        except (json.JSONDecodeError, OSError):
            self._save_settings(FACTORY_SETTINGS)
            return dict(FACTORY_SETTINGS)

    def _save_current_settings(self) -> None:
        """Writes current settings to disk and saved_settings variable."""
        data = {
            "ws_address": self.ws_address,
            "sensors": self.sensors,
            "input_disconnected_label": self.input_disconnected_label,
            "output_disconnected_label": self.output_disconnected_label,
            "default_sample_rate": self.default_sample_rate,
            "default_patch": self.default_patch.get(),
            "saved_patches_list": self.saved_patches_list,
            "default_device": self.default_device.get(),
            "default_outport": self.default_outport.get()
        }

        self._save_settings(data)
        self.saved_settings = data

    def _factory_settings_reset(self) -> None:
        """Resets all settings to factory defaults."""
        data = FACTORY_SETTINGS

        self._save_settings(data)

    def _load_patches(self) -> dict:
        """Loads patches from disk, creating a file from factory patches if missing."""
        # create directory and new patches file if missing
        if not os.path.exists(self.patches_filepath):
            os.makedirs(os.path.dirname(self.patches_filepath), exist_ok=True) 
            with open(self.patches_filepath, 'w') as OUTFILE:
                json.dump(FACTORY_PATCHES, OUTFILE, indent=4)
            return dict(FACTORY_PATCHES)
        else:
            with open(self.patches_filepath, 'r') as INFILE:
                return json.load(INFILE)

    def _write_default_device(self, *args):
        """Writes new default device to settings.json."""
        self.saved_settings["default_device"] = self.default_device.get()
        self._save_settings(self.saved_settings)

    def _write_default_outport(self, *args):
        """Writes new default ouport to settings.json."""
        self.saved_settings["default_outport"] = self.default_outport.get()
        self._save_settings(self.saved_settings)

    def _write_default_patch(self, *args):
        """Writes new default patch to settings.json."""
        self.saved_settings["default_patch"] = self.default_patch.get()
        self._save_settings(self.saved_settings)






