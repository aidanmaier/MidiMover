import tkinter as tk
import os
import json

# Settings filepaths
DATA_FOLDER_FILEPATH = './app_data/'
SETTINGS_FILENAME = 'settings.json'
SETTINGS_FILEPATH = DATA_FOLDER_FILEPATH + SETTINGS_FILENAME

# Hardcoded backup default settings, immutable from within app
FACTORY_SETTINGS = {
    "ws_address" : "_websocket._tcp.local.",
    "sensors" : ["rotation_vector", "linear_acceleration"],
    "input_disconnected_label" : "< Connect Device >",
    "output_disconnected_label" : "< Connect MIDI Port >",
    "default_sample_rate" : 50,

    "default_patch" : "Default Patch",
    "saved_patches_list" : ["Patch 1", "Patch 2"],
    "default_device" : "SensorServer._websocket._tcp.local.",
    "default_outport" : "IAC Driver Bus 1"
}

class Settings:
    """Shared config for global settings."""
    # Settings object passed to all gui components so all variables are settable locally
    # tk variables refire when updated
    def __init__(self):

        self.saved_settings = self._load_settings()
        s = self.saved_settings

        # Saved settings, load factory setting if missing
        self.ws_address = s.get('ws_address', FACTORY_SETTINGS['ws_address'])
        self.sensors = s.get('sensors', FACTORY_SETTINGS['sensors'])
        self.input_disconnected_label = s.get('input_disconnected_label', FACTORY_SETTINGS['input_disconnected_label'])
        self.output_disconnected_label = s.get('output_disconnected_label', FACTORY_SETTINGS['output_disconnected_label'])
        self.default_sample_rate = s.get('default_sample_rate', FACTORY_SETTINGS['default_sample_rate'])
        self.default_patch = tk.StringVar(value=s.get('default_patch', FACTORY_SETTINGS['default_patch']))
        self.saved_patches_list = s.get('saved_patches_list', FACTORY_SETTINGS['saved_patches_list'])
        self.default_device = tk.StringVar(value=s.get('default_device', FACTORY_SETTINGS['default_device']))
        self.default_outport = tk.StringVar(value=s.get('default_outport', FACTORY_SETTINGS['default_outport']))

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

        self.loaded_patch = tk.StringVar(value='')

    def _load_settings(self) -> dict:
        """Loads settings from disk, creating a file from factory settings if missing."""

        # create directory and new settings file if missing
        if not os.path.exists(SETTINGS_FILEPATH):
            os.makedirs(os.path.dirname(SETTINGS_FILEPATH), exist_ok=True) 
            with open(SETTINGS_FILEPATH, 'w') as OUTFILE:
                json.dump(FACTORY_SETTINGS, OUTFILE, indent=4)
            return dict(FACTORY_SETTINGS)
        else:
            with open(SETTINGS_FILEPATH, 'r') as INFILE:
                return json.load(INFILE)

    def _save_settings(self, data: dict) -> None:
        """Writes settings to disk and saved_settings variable."""

        os.makedirs(os.path.dirname(SETTINGS_FILEPATH), exist_ok=True)  # create directory if does not exist
        with open(SETTINGS_FILEPATH, 'w') as OUTFILE:
            json.dump(data, OUTFILE, indent=4)
            
        self.saved_settings = data

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


    def _factory_reset(self):
        """Resets all settings to factory defaults."""

        data = FACTORY_SETTINGS
        self._save_settings(data)