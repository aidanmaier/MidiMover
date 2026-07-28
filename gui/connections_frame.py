import tkinter as tk
from tkinter import ttk
from gui.device_frame import DeviceFrame
from gui.midi_frame import MidiFrame

class ConnectionsFrame(ttk.Frame):
    """GUI container for input and output connection configuration."""

    def __init__(self, container, settings):
        super().__init__(container)

        # Pointers to global settings
        self.settings = settings
        self.running_status = self.settings.running_status

        # Local constants
        self.name = 'Connections'

        self._create_widgets()

        # Handle connection settings buttons
        self.running_status.trace_add('write', self._update_connections_settings_state)
        self._update_connections_settings_state()


    def _create_widgets(self):
        # Device connections
        self.device_frame = DeviceFrame(self, self.settings)
        self.device_frame.pack(fill='x', pady=(5, 0))

        # Separate device and midi connections
        self.seperator_upper = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.seperator_upper.pack(fill='x', padx=10, pady=(15, 5))

        # Midi connections
        self.midi_frame = MidiFrame(self, self.settings)
        self.midi_frame.pack(fill='x')

        # Separate connections from settings
        self.seperator_lower = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.seperator_lower.pack(fill='x', padx=10, pady=(15, 5))

        # Connection settings
        self.connection_settings_frame = ttk.Frame(self)
        self.connection_settings_frame.pack(fill='x', padx=(10, 20), pady=10)

        self.refresh_button = ttk.Button(self.connection_settings_frame, text='Refresh Lists', command=self._refresh_lists)
        self.refresh_button.pack(side='right')

        self.reset_button = ttk.Button(self.connection_settings_frame, text='Reset All', command=self._reset_settings)
        self.reset_button.pack(side='right', padx=10)
        
        self.sample_rate_label = ttk.Label(self.connection_settings_frame, text='Sample Rate:')
        self.sample_rate_label.pack(side='left')
        self.sample_rate_spinbox = ttk.Spinbox(self.connection_settings_frame)
        self.sample_rate_spinbox.pack(side='left', fill='none')
        self.hz_label = ttk.Label(self.connection_settings_frame, text='Sample Rate:')
        self.hz_label.pack(side='left')

    def _update_connections_settings_state(self, *args):
        """Disables connectinos settings controls if running."""
        running = self.running_status.get()
        if running:
            self.refresh_button.config(state='disabled')
            self.reset_button.config(state='disabled')
        else:
            self.refresh_button.config(state='normal')
            self.reset_button.config(state='normal')
    
    def _refresh_lists(self):
        """Refreshes input and output devices lists."""
        self.device_frame._refresh_devices_list()
        self.midi_frame._refresh_devices_list()

    def _reset_settings(self):
        """Reset all settings to factory defaults."""
        self.settings._factory_settings_reset()


