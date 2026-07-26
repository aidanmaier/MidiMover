import tkinter as tk
from tkinter import ttk
from typing import Callable

class ConfigFrame(ttk.Frame):
    """Generic GUI container for configuring external connections."""

    def __init__(
            self, 
            container, 
            name,
            settings, 
            device_type,
            get_devices: Callable, 
            connect_device: Callable, 
            disconnect_device: Callable,
            default_device_var: tk.StringVar,
            connection_var: tk.StringVar,
            connection_name_var: tk.StringVar,
            connection_status_var: tk.BooleanVar,
            disconnected_label: str
        ):

        super().__init__(container)

        # Pointers to global settings
        self.settings = settings
        self.default_device_var = default_device_var
        self.connection_var = connection_var
        self.connection_name_var = connection_name_var
        self.connection_status_var = connection_status_var
        self.disconnected_label = disconnected_label
        self.running_status = self.settings.running_status

        # Local constants
        self.name = name
        self.device_type = device_type
        self.get_devices = get_devices
        self.connect_device = connect_device
        self.disconnect_device = disconnect_device
        self.options = {'sticky': 'w', 'padx':10, 'pady':(10, 5)} # widget placement options
        self.refresh_interval = 2000 # poll rate for finding available devices (ms)

        # Local variables
        self.available_devices = []
        self.selected_device_name = None
        self.connection_state = False # connection state flag
        self.connected_device = None
        self.connected_device_name = None
        self.default_device = self.default_device_var.get()

        # Configure columns
        for i in range(2):
            self.columnconfigure(i, weight=10)
        self.columnconfigure(2, weight=1)

        self._create_widgets()
        self.bind('<Destroy>', self._on_destroy)
        self._refresh_devices_list()

        # Manage command from global connect
        self.running_status.trace_add('write', self._on_running_status_change)

    def _create_widgets(self):
        # Available MIDI devices list
        self.devices_label = ttk.Label(self, text='Available Devices:')
        self.devices_label.grid(column=0, row=0, **self.options)

        self.refresh_button = ttk.Button(self, text='Refresh', command=self._refresh_devices_list)
        self.refresh_button.grid(column=1, row=0, sticky='e', padx=0, pady=(10, 5))

        self.devices_list = ttk.Treeview(self, columns=('device','status', 'default'), show='headings', height=6, selectmode='browse')
        self.devices_list.heading('device', text=f'{self.device_type} Name')
        self.devices_list.column('device', width=200, anchor='w')
        self.devices_list.heading('status', text='Connection Status')
        self.devices_list.column('status', width=60, anchor='w')
        self.devices_list.heading('default', text=f'Default {self.device_type}')
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
        self.set_default_button = ttk.Button(self, text=f'Set as Default {self.device_type}', state='disabled', command=self._on_set_default)
        self.set_default_button.grid(column=1, row=3, sticky='e', padx=0, pady=(10, 5))

    def _update_connection_button_states(self):
        """Updates connection and default button states based on selection and connection."""
        # Connection button logic
        if self.connection_state:
            self.connect_button.config(state='normal')
        elif self.selected_device_name:
            self.connect_button.config(state='normal')
        else:
            self.connect_button.config(state='disabled')

        # Set Default button logic
        if self.selected_device_name and self.selected_device_name != self.default_device:
            self.set_default_button.config(state='normal')
        else:
            self.set_default_button.config(state='disabled')

    def _set_status(self, state: bool):
        """Sets connection status label and button states."""
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
        """Captures selected item name."""
        selected_items = self.devices_list.selection()
        if not selected_items:
            self.selected_device_name = None
            self._update_connection_button_states()
            return

        selected_item = selected_items[0] # full device name (iid)
        tags = self.devices_list.item(selected_item, 'tags')
        # Make unavailable items non-selectable
        if 'unavailable' in tags:
            self.devices_list.selection_remove(selected_item)
            self.selected_device_name = None
            self._update_connection_button_states()
            return

        # values = self.devices_list.item(selected_item, 'values')
        # device_name = values[0] if values else None
        # self.selected_device_name = None if device_name == None else device_name

        self.selected_device_name = selected_item

        self._update_connection_button_states()

    def _on_set_default(self):
        """Makes the selected MIDI output device the new default device."""
        if not self.selected_device_name:
            return
        self.default_device = self.selected_device_name # update local setting
        self.default_device_var.set(self.selected_device_name) # update global setting
        self._refresh_devices_list()

    def _on_running_status_change(self, *args):
        running = self.running_status.get()
        if running:
            self._connect_device()
        else:
            self._disconnect_device()

    def _connect_device(self):
        """Opens connection with selected device."""

        # Check if already connected
        if self.connection_status_var.get():
            return

        # Connect to selected device
        self.connected_device_name = self.selected_device_name
        self.connected_device = self.connect_device(self) # call connect function

        self._set_status(True) # update local setting
        self.connection_var.set(str(self.selected_device_name)) # update global settings
        self.connection_name_var.set(str(self.selected_device_name).removesuffix('.' + self.settings.ws_address))
        self.connection_status_var.set(True)
        self._refresh_devices_list()

    def _on_connect_failed(self, device_name, exc):
        """ Called when a background connection attempt fails. Resets state safely. """
        if self.connected_device_name != device_name:
            return

        self._set_status(False)
        self.connection_var.set('')
        self.connection_name_var.set(str(self.disconnected_label))
        self.connection_status_var.set(False)
        self._refresh_devices_list()
        
    def _disconnect_device(self):
        """Disconnects active device."""
        device = self.connected_device
        if device:
            self.disconnect_device(self) # call disconnect function
            self._set_status(False) # update local setting
            self.connection_var.set('') # update global settings
            self.connection_name_var.set(str(self.disconnected_label))
            self.connection_status_var.set(False)
            self._refresh_devices_list()

    def _focus_list(self):
            """Focuses selection on the connected or default item if present."""
            focus_item = None

            # List focus priority: connected -> selected -> default
            if self.connection_state:
                focus_name = self.connected_device_name
            elif self.selected_device_name:
                focus_name = self.selected_device_name
            elif self.default_device:
                focus_name = self.default_device
            else:
                focus_name = None

            # Connection var priority: connected -> default
            if self.connection_state:
                connection = self.connected_device_name
            elif self.default_device and self.default_device in self.available_devices:
                connection = self.default_device
            else:
                connection = None

            # Update global settings
            if connection is None:
                self.connection_var.set('')
                self.connection_name_var.set(str(self.disconnected_label))
            else:
                self.connection_var.set(connection)
                self.connection_name_var.set(connection.removesuffix('.' + self.settings.ws_address))

            # Match device name (iid) to list item
            if focus_name and self.devices_list.exists(focus_name):
                focus_item = focus_name

            # Focus list item, update selection and button states
            if focus_item:
                self.devices_list.selection_set(focus_item)
                self.devices_list.focus(focus_item)
                self.devices_list.see(focus_item)
                self.selected_device_name = focus_name

            self._update_connection_button_states()
                

    def _refresh_devices_list(self):
        """Clears devices list and rescans for available devices."""
        # Check for current refresh job
        if getattr(self, '_refresh_job', None):
            self.after_cancel(self._refresh_job)

        # Delete all list children
        for item in self.devices_list.get_children():
            self.devices_list.delete(item)

        # Scan for available devices
        self.available_devices = self.get_devices(self) # call get devices function
        if not self.available_devices:
            self.available_devices = []

        # Add available devices to list with default connection status
        # Strip '._websocket._tcp.local.' suffix from name for display
        for connection in self.available_devices:
            default_status = ''
            if connection == self.default_device:
                default_status = 'Default'
            if connection == self.connected_device_name:
                self.devices_list.insert(
                    '', 
                    tk.END, 
                    iid=connection,
                    values=(connection.removesuffix('._websocket._tcp.local.'), 'Connected', default_status), 
                    tags=('connected',))
            else:
                self.devices_list.insert(
                    '', 
                    tk.END, 
                    iid=connection,
                    values=(connection.removesuffix('._websocket._tcp.local.'), 'Available', default_status), 
                    tags=('unconnected',))

        # If default device unavailable, flag in list
        if self.default_device and self.default_device not in self.available_devices:
            self.devices_list.insert(
                '', 
                tk.END, 
                iid=self.default_device,
                values=(self.default_device.removesuffix('._websocket._tcp.local.'), 'Unavailable', 'Default'), 
                tags=('unavailable',))

        # Focus on connected or default item
        self._focus_list()

        # Call self after refresh interval
        self._refresh_job = self.after(self.refresh_interval, self._refresh_devices_list)

    def _on_destroy(self, event):
        """Cleanup handler before closing."""
        if event.widget is not self:
            return

        # Cancel any refresh jobs
        if getattr(self, '_refresh_job', None):
            self.after_cancel(self._refresh_job)

        # Close any connection
        if self.connection_state and self.connected_device:
            self.disconnect_device(self)



