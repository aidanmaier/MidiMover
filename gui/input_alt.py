import threading
import tkinter as tk
from tkinter import ttk
from zeroconf import Zeroconf, ServiceBrowser
from logic.listen import WebsocketServiceListener

class ConnectionFrame(ttk.Frame):
    """ GUI container for configuring input device connections. """
    
    def __init__(self, container, settings):
        super().__init__(container)
        self.name = 'Connect Device'
        self.settings = settings
        self.options = {'sticky': 'w', 'padx':10, 'pady':(10, 5)} # widgit placement options
        self.refresh_interval = 2000 # poll rate for finding available devices (ms)

        self.default_device_name = settings.default_device.get()
        self.available_devices = []
        self.selected_device_name = None
        self.connection_state = False # connection state flag
        self.connected_device = None
        self.connected_device_name = None

        self._refresh_job = None
        self._connect_thread = None

        self.sensors = self.settings.sensors
        self.zeroconf = Zeroconf() # zeroconf listener records available devices
        self.listener = WebsocketServiceListener(self.sensors)
        self.browser = ServiceBrowser(self.zeroconf, self.settings.ws_address, self.listener)

        # Configure columns
        for i in range(2):
            self.columnconfigure(i, weight=10)
        self.columnconfigure(2, weight=1)

        self._create_widgets()
        self.bind('<Destroy>', self._on_destroy)
        self._refresh_devices_list()

    def _create_widgets(self):
        # Available devices list
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
        self.devices_list.bind('<<TreeviewSelect>>', self._on_device_select)

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
        self.set_default_button = ttk.Button(self, text='Set as Default Device', state='disabled', command=self._on_set_default)
        self.set_default_button.grid(column=1, row=3, sticky='e', padx=0, pady=(10, 5))

    def _update_connection_button_states(self):
        """ Updates connection and default button states based on selection and connection. """
        # Connection button logic
        if self.connection_state:
            self.connect_button.config(state='normal')
        elif self.selected_device_name:
            self.connect_button.config(state='normal')
        else:
            self.connect_button.config(state='disabled')

        # Set Default button logic
        if self.selected_device_name and self.selected_device_name != self.default_device_name:
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

    def _on_device_select(self, event=None):
        """ Captures selected output port name. """
        selection = self.devices_list.selection()
        self.selected_device_name = selection[0] if selection else None
        self._update_connection_button_states()

    def _on_set_default(self):
        """ Makes the selected device the new default device. """
        if not self.selected_device_name:
            return
        
        self.default_device_name = self.selected_device_name # update local setting
        self.settings.default_device.set(self.selected_device_name) #update global setting
        self._refresh_devices_list()

    def _connect_device(self):
        """ Connects to the selected websocket device on a background thread. """
        # Ignore if no selected device or already connected
        if not self.selected_device_name or self.connection_state:
            return

        device = self.selected_device_name
        self.connected_device = self.listener.discovered_services.get(device)
        self.connected_device_name = device.removesuffix('._websocket._tcp.local.')

        self._connect_thread = threading.Thread(
            target=self.listener.connect_to_service,
            args=(device,),
            daemon=True,
        )
        self._connect_thread.start()

        self._set_status(True)
        self._refresh_devices_list()

    def _disconnect_device(self):
        self.listener.disconnect()
        self._set_status(False)
        self._refresh_devices_list()

    def _focus_list(self):
        """ Focuses selection on the connected or default item if present. """
        focus_name = None
        focus_item = None
        # Priority: connected -> selected -> default
        if self.connection_state:
            focus_name = self.connected_device_name
        elif self.selected_device_name:
            focus_name = self.selected_device_name
        elif self.default_device_name:
            focus_name = self.default_device_name
        # Update global settings
        if focus_name == None:
            self.settings.output_connection.set('< Connect MIDI Port >')
        else:
            self.settings.output_connection.set(focus_name)
        # Match port name to list item
        for item in self.devices_list.get_children():
            values = self.devices_list.item(item, 'values')
            if values and values[0] == focus_name:
                focus_item = item
                break
        # Focus list item, update selection and button states
        if focus_item:
            self.devices_list.selection_set(focus_item)
            self.devices_list.focus(focus_item)
            self.devices_list.see(focus_item)
            self.selected_device_name = self.default_device_name
            self._update_connection_button_states()

    def _refresh_devices_list(self):
        """ Clears devices list . """
        if self._refresh_job is not None:
            self.after_cancel(self._refresh_job)
            self._refresh_job = None

        # Delete all list children
        for item in self.devices_list.get_children():
            self.devices_list.delete(item)

        # Scan for available devices
        self.available_devices = self.listener.get_available_devices()
        if not self.available_devices:
            self.available_devices = []

        # Add available devices to list with default connection status
        for connection in self.available_devices:
            default_status = ''
            if connection == self.default_device_name:
                default_status = 'Default'
            if connection == self.connected_device_name:
                self.devices_list.insert('', tk.END, values=(connection, 'Connected', default_status), tags=('connected',))
            else:
                self.devices_list.insert('', tk.END, values=(connection, 'Available', default_status), tags=('unconnected',))

        # If default device unavailable, flag in list
        if self.default_device_name and self.default_device_name not in self.available_devices:
            self.devices_list.insert('', tk.END, values=(self.default_device_name, 'Unavailable', 'Default'), tags=('unavailable',))

        # Focus on connected or default item
        self._focus_list()

        # Call self after refresh interval
        self._refresh_job = self.after(self.refresh_interval, self._refresh_devices_list)

    def _on_destroy(self, event):
        """ Cleanup handler, closes Zeroconf before closing. """
        if event.widget is not self:
            return
        if self._refresh_job is not None:
            self.after_cancel(self._refresh_job)
            self._refresh_job = None
        self.zeroconf.close()