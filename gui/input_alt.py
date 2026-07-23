import tkinter as tk
from tkinter import ttk
from logic.ws_config import WebsocketServiceListener

class ConnectionFrame(ttk.Frame):
    """ GUI container for configuring input device connections. """
    
    def __init__(self, container, settings):
        super().__init__(container)
        self.name = 'Connect Device'
        self.settings = settings
        self.options = {'sticky': 'w', 'padx':10, 'pady':(10, 5)} # widgit placement options

        self.default_device_name = settings.default_device.get()
        self.available_devices = []
        self.selected_device = None
        self.connection_state = False # connection state flag
        self.connected_device = None
        self.connected_device_name = None

        # Configure columns
        for i in range(2):
            self.columnconfigure(i, weight=10)
        self.columnconfigure(2, weight=1)

        self._create_widgets()
        self._refresh_devices_list()

    def _create_widgets(self):
        # Available MIDI devices list
        self.devices_label = ttk.Label(self, text='Available Devices:')
        self.devices_label.grid(column=0, row=0, **self.options)

        self.refresh_button = ttk.Button(self, text='Refresh', command=self._refresh_devices_list)
        self.refresh_button.grid(column=1, row=0, sticky='e', padx=0, pady=(10, 5))

        self.devices_list = ttk.Treeview(self, columns=('port','status', 'default'), show='headings', height=6, selectmode='browse')
        self.devices_list.heading('port', text='Device Name')
        self.devices_list.column('port', width=200, anchor='w')
        self.devices_list.heading('status', text='Connection Status')
        self.devices_list.column('status', width=60, anchor='w')
        self.devices_list.heading('default', text='Default Device')
        self.devices_list.column('default', width=40, anchor='w')
        self.devices_list.grid(column=0, row=2, columnspan=2, padx=(10, 0), pady=0, sticky='nsew')
        # self.devices_list.bind('<<TreeviewSelect>>', self._on_device_select)

        # Scrollbar linked to devices list
        self.devices_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.devices_list.yview)
        self.devices_scrollbar.grid(column=2, row=2, padx=0, pady=0, sticky='ns')
        self.devices_list.config(yscrollcommand=self.devices_scrollbar.set)

        # List item colour tags
        self.devices_list.tag_configure('unconnected', foreground='blue')
        self.devices_list.tag_configure('connected', foreground='green')
        self.devices_list.tag_configure('unavailable', foreground='red')
        
        # Connection buttons
        self.connect_button = ttk.Button(self, text='Connect', state='disabled', command=self._connect_device)
        self.connect_button.grid(column=0, row=3, **self.options)
        self.set_default_button = ttk.Button(self, text='Set as Default Port', state='disabled', command=self._on_set_default)
        self.set_default_button.grid(column=1, row=3, sticky='e', padx=0, pady=(10, 5))

    def _update_connection_button_states(self):
            """ Updates connection and default button states based on selection and connection. """
            # Connection button logic
            if self.connection_state:
                self.connect_button.config(state='normal')
            elif self.selected_device:
                self.connect_button.config(state='normal')
            else:
                self.connect_button.config(state='disabled')
            # Set Default button logic
            if self.selected_device and self.selected_device != self.default_device_name:
                self.set_default_button.config(state='normal')
            else:
                self.set_default_button.config(state='disabled')

    def _set_status(self, state: bool):
        """ Sets connection status label and button states. """
        connection = self.connection_state = state
        if connection:
            self.refresh_button.config(state='disabled')
            self.connect_button.config(text='Disconnect', command=self._disconnect_device)
            self.devices_list.config(selectmode='none')
            self._update_connection_button_states()
        else:
            self.refresh_button.config(state='normal')
            self.connect_button.config(text='Connect', command=self._connect_device)
            self.devices_list.config(selectmode='browse')
            self.connected_device = None
            self.connected_device_name = None
            self._update_connection_button_states()

    def _on_device_select(self):
        pass

    def _connect_device(self):
        pass

    def _disconnect_device(self):
            pass

    def _on_set_default(self):
        pass

    def _refresh_devices_list(self):
        pass