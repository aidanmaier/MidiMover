import tkinter as tk
import os
import json

# Hardcoded backup defaults, immutable from within app
FACTORY_SETTINGS = {
    "ws_address" : "_websocket._tcp.local.",
    "sensors" : ["rotation_vector", "linear_acceleration"],
    "input_disconnected_label" : "< Connect Device >",
    "output_disconnected_label" : "< Connect MIDI Port >",
    "default_sample_rate" : 50,
    "default_patch" : "Default Patch",
    "saved_patches_list" : [],
    "default_device" : "SensorServer._websocket._tcp.local.",
    "default_outport" : "IAC Driver Bus 1"
}

FACTORY_PATCHES = {
    "patches" : {
        "< New Patch >" : {
            "description": "A blank patch.",
            "parameters" : {
                "0" : {
                    "input" : None,
                    "input_range" : [],
                    "output" : None,
                    "output_range" : []
                },
                "1" : {
                    "input" : None,
                    "input_range" : [],
                    "output" : None,
                    "output_range" : []
                },
                "2" : {
                    "input" : None,
                    "input_range" : [],
                    "output" : None,
                    "output_range" : []
                }
            }
        }
    }
}

class Settings:
    """Shared config for global settings."""
    # Settings object passed to all gui components so all variables are settable locally
    # tk variables refire when updated
    def __init__(self, settings_filepath, patches_filepath):
        self.settings_filepath = settings_filepath
        self.patches_filepath = patches_filepath

        self.saved_settings = self._load_settings()
        s = self.saved_settings

        self.saved_patches_data = self._load_patches()
        p = self.saved_patches_data

        # Immutable app settings
        self.input_parameter_types = ['Speed', 'Pitch', 'Yaw', 'Roll'] # plus 'Width', 'Height', 'Depth'
        self.output_parameter_types = ['Note', 'Bend', 'Volume', 'Filt Res', 'Filt Cut']

        self.ws_address: str = FACTORY_SETTINGS['ws_address']
        self.sensors: list[str] = FACTORY_SETTINGS['sensors']
        self.input_disconnected_label: str = FACTORY_SETTINGS['input_disconnected_label']
        self.output_disconnected_label: str = FACTORY_SETTINGS['output_disconnected_label']

        # User settings, load factory setting if missing
        self.default_sample_rate = s.get('default_sample_rate', FACTORY_SETTINGS['default_sample_rate'])
        self.default_patch = tk.StringVar(value=s.get('default_patch', FACTORY_SETTINGS['default_patch']))
        self.default_device = tk.StringVar(value=s.get('default_device', FACTORY_SETTINGS['default_device']))
        self.default_outport = tk.StringVar(value=s.get('default_outport', FACTORY_SETTINGS['default_outport']))

        self.saved_patches_list = list(p['patches'].keys())

        # Runtime variables
        self.sample_rate = tk.IntVar(value=self.default_sample_rate)
        self.connection_status = tk.StringVar(value='Unconnected')
        self.running_status = tk.BooleanVar(value=False)
        self.tabs_visible = tk.BooleanVar(value=True)

        self.input_connection = tk.StringVar(value='')
        self.input_connection_name = tk.StringVar(value=self.input_disconnected_label)
        self.input_connection_status = tk.BooleanVar(value=False)

        self.output_connection = tk.StringVar(value='')
        self.output_connection_name = tk.StringVar(value=self.output_disconnected_label)
        self.output_connection_status = tk.BooleanVar(value=False)

        self.loaded_patch_name = tk.StringVar(value='')
        self.loaded_patch_description = tk.StringVar(value='')
        self.loaded_patch_parameters_data = {}

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

    def _save_patch(self) -> None:
        pass

    def _factory_patches_reset(self) -> None:
        pass