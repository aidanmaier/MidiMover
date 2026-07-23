import tkinter as tk
from tkinter import ttk

class StatusBar(ttk.Frame):
    """ Top-level status bar showing connection status. """

    def __init__(self, container, settings):
        super().__init__(container)
        self.settings = settings
        self.options = {'sticky':'w', 'padx':10, 'pady':(10, 5)} # widgit placement options

        # Configure columns
        self.columnconfigure(0, weight=2)
        for i in range(1, 5):
            self.columnconfigure(i, weight=1)

        for i in range(2):
                    self.rowconfigure(i, weight=1)

        self._create_widgets()

    def _create_widgets(self):

        self.start_button = ttk.Button(self, text='START', command=self._on_start_button)
        self.start_button.grid(column=0, row=0, **self.options)

        self.input_label = ttk.Label(self, text='Device:')
        self.input_label.grid(column=1, row=0, **self.options)
        self.input_status = ttk.Label(self, textvariable=self.settings.input_connection)
        self.input_status.grid(column=2, row=0, **self.options)

        # Output information
        self.output_label = ttk.Label(self, text='MIDI Port:')
        self.output_label.grid(column=3, row=0, **self.options)
        self.output_status = ttk.Label(self, textvariable=self.settings.output_connection)
        self.output_status.grid(column=4, row=0, **self.options)

        self.test_label = ttk.Label(self, text='TEST')
        self.test_label.grid(column=1, row=1, **self.options)

        # Keep output status colors in sync with connection state
        self.settings.input_connection.trace_add('write', self._update_input_status_color)
        self.settings.input_connection_status.trace_add('write', self._update_input_status_color)
        self._update_input_status_color()

        self.settings.output_connection.trace_add('write', self._update_output_status_color)
        self.settings.output_connection_status.trace_add('write', self._update_output_status_color)
        self._update_output_status_color()

    def _on_start_button(self):
        running = self.settings.running_status.get()
        if not running:
            self.settings.running_status.set(True)
            self.start_button.config(text='STOP')
        else:
            self.settings.running_status.set(False)
            self.start_button.config(text='START')

    def _update_input_status_color(self, *args):
        """ Status colors: red = unconnected, blue = default port, green = connected port. """
        name = self.settings.input_connection.get()
        connected = self.settings.input_connection_status.get()

        if name == '< Connect Device >':
            color = 'red'
        elif connected:
            color = 'green'
        else:
            color = 'blue'

        self.input_status.config(foreground=color)

    def _update_output_status_color(self, *args):
        """ Status colors: red = unconnected, blue = default port, green = connected port. """
        name = self.settings.output_connection.get()
        connected = self.settings.output_connection_status.get()

        if name == '< Connect MIDI Port >':
            color = 'red'
        elif connected:
            color = 'green'
        else:
            color = 'blue'

        self.output_status.config(foreground=color)

