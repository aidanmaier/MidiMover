import tkinter as tk
from tkinter import ttk

class StatusBar(ttk.Frame):
    """Top-level status bar showing connection status."""

    def __init__(self, container, settings):
        super().__init__(container)
        self.settings = settings

        # Pointers to global settings
        self.input_settings = {
             'connection_name': self.settings.input_connection_name,
             'connection_status': self.settings.input_connection_status,
             'disconnected_label': self.settings.input_disconnected_label,
        }
        self.output_settings = {
             'connection_name': self.settings.output_connection_name,
             'connection_status': self.settings.output_connection_status,
             'disconnected_label': self.settings.output_disconnected_label             
        }

        self.options = {'sticky':'w', 'padx':10, 'pady':(10, 5)} # widgit placement options

        # Configure columns
        self.columnconfigure(0, weight=2)
        for i in range(1, 5):
            self.columnconfigure(i, weight=1)

        for i in range(2):
                    self.rowconfigure(i, weight=1)

        self._create_widgets()

        # Keep output status colors in sync with connection state
        self._create_status_tracer(self.input_settings['connection_name'], self.input_status_label, **self.input_settings)
        self._create_status_tracer(self.input_settings['connection_status'], self.input_status_label, **self.input_settings)
        self._update_status(self.input_status_label, **self.input_settings)
    
        self._create_status_tracer(self.output_settings['connection_status'], self.output_status_label, **self.output_settings)
        self._create_status_tracer(self.output_settings['connection_name'], self.output_status_label, **self.output_settings)
        self._update_status(self.output_status_label, **self.output_settings)

    def _create_widgets(self):
        # Start/Stop buttons
        self.start_button = ttk.Button(self, text='START', command=self._on_start_button)
        self.start_button.grid(column=0, row=0, **self.options)

        self.input_label = ttk.Label(self, text='Device:')
        self.input_label.grid(column=1, row=0, **self.options)
        self.input_status_label = ttk.Label(self, textvariable=self.settings.input_connection_name)
        self.input_status_label.grid(column=2, row=0, **self.options)

        # Output information
        self.output_label = ttk.Label(self, text='MIDI Port:')
        self.output_label.grid(column=3, row=0, **self.options)
        self.output_status_label = ttk.Label(self, textvariable=self.settings.output_connection_name)
        self.output_status_label.grid(column=4, row=0, **self.options)

        self.test_label = ttk.Label(self, text='TEST')
        self.test_label.grid(column=1, row=1, **self.options)

    def _create_status_tracer(self, variable: tk.Variable, label: ttk.Label, **global_settings) -> None:
            """Creates a global variable tracer and assigns it to a label"""
            variable.trace_add(
                'write',
                lambda *args: self._update_status(status_label=label, **global_settings)
            )

    def _update_status(self, status_label: ttk.Label, connection_name: tk.StringVar, connection_status: tk.BooleanVar, disconnected_label: str) -> None:
        """Updates connection status label with correct color."""
        name = connection_name.get()
        if name == disconnected_label: # no default or connected device available
            color = 'red'
        elif connection_status.get(): # device connected
            color = 'green'
        else:
            color = 'blue' # default device available but unconnected
        status_label.config(foreground=color, text=name)

    def _on_start_button(self):
        running = self.settings.running_status.get()
        if not running:
            self.settings.running_status.set(True)
            self.start_button.config(text='STOP')
        else:
            self.settings.running_status.set(False)
            self.start_button.config(text='START')

