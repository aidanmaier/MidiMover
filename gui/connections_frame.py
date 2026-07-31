import tkinter as tk
from tkinter import ttk
from gui.device_frame import DeviceFrame
from gui.midi_frame import MidiFrame

class ConnectionsFrame(ttk.Frame):
    """GUI container for input and output connection configuration."""

    def __init__(self, container, settings, listener, midi_out):
        super().__init__(container)

        # Pointers to global settings
        self.settings = settings
        self.running_status: tk.BooleanVar = self.settings.running_status
        self.selected_input: tk.StringVar = self.settings.selected_input
        self.selected_output: tk.StringVar = self.settings.selected_output

        # Local constants
        self.name = 'Connections'
        self.listener = listener
        self.midi_out = midi_out

        # Configure grid
        for i in range(2):
            self.columnconfigure(i, weight=1)

        self._create_widgets()

        # Handle connection settings buttons
        self.running_status.trace_add('write', self._update_connections_settings_state)
        self._update_connections_settings_state()

        # Handle changes in selected IO devices
        self.device_frame.selected_device_name.trace_add('write', self._set_selected_input)
        self.midi_frame.selected_device_name.trace_add('write', self._set_selected_output)

    def _create_widgets(self):
        # Device connections
        self.device_frame = DeviceFrame(self, self.settings, self.listener) # pass listener to gui
        self.device_frame.grid(column=0, row=0, sticky='ew', padx=10, pady=10)

        # Midi connections
        self.midi_frame = MidiFrame(self, self.settings, self.midi_out) # pass midi_out to gui
        self.midi_frame.grid(column=1, row=0, sticky='ew', padx=(0, 20), pady=10)

        self.refresh_button = ttk.Button(self, text='Refresh Lists', command=self._refresh_lists)
        self.refresh_button.grid(column=1, row=2, sticky='e', padx=(10, 20))

        # Separate connections from settings
        self.seperator_lower = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.seperator_lower.grid(column=0, row=3, columnspan=2, sticky='ew', padx=20, pady=(15, 5))

        # Connection settings TODO
        self.connection_settings_frame = ttk.Frame(self)
        self.connection_settings_frame.grid(column=0, row=3, columnspan=2, padx=(10, 20), pady=10)

        # self.reset_button = ttk.Button(self.connection_settings_frame, text='Reset All', command=self._reset_settings)
        # self.reset_button.pack(side='right', padx=10)
        
        # self.sample_rate_label = ttk.Label(self.connection_settings_frame, text='Sample Rate:')
        # self.sample_rate_label.pack(side='left')
        # self.sample_rate_spinbox = ttk.Spinbox(self.connection_settings_frame)
        # self.sample_rate_spinbox.pack(side='left', fill='none')
        # self.hz_label = ttk.Label(self.connection_settings_frame, text='Sample Rate:')
        # self.hz_label.pack(side='left')

    def _update_connections_settings_state(self, *args):
        """Disables connectinos settings controls if running."""
        running = self.running_status.get()
        if running:
            self.refresh_button.config(state='disabled')
            # self.reset_button.config(state='disabled')
        else:
            self.refresh_button.config(state='normal')
            # self.reset_button.config(state='normal')
    
    def _set_selected_input(self, *args) -> None:
        """Passes the input menu selection to global settings."""
        new_selected_device = self.device_frame.selected_device_name.get()
        self.selected_input.set(new_selected_device)

    def _set_selected_output(self, *args) -> None:
        """Passes the output menu selection to global settings."""
        new_selected_outport = self.midi_frame.selected_device_name.get()
        self.selected_output.set(new_selected_outport)
    
    def _refresh_lists(self):
        """Refreshes input and output devices lists."""
        self.device_frame._refresh_devices_list()
        self.midi_frame._refresh_devices_list()

    def _reset_settings(self):
        """Reset all settings to factory defaults."""
        self.settings._factory_settings_reset()


