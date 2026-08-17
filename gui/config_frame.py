import tkinter as tk
from tkinter import ttk
import threading
import mido as md # type supressions needed for Backend methods
from typing import Callable
from zeroconf import Zeroconf, ServiceBrowser

from settings import Settings
from input import WebsocketServiceListener
from output import MidiOut

class ConfigFrame(ttk.Frame):
    """Generic GUI container for configuring external connections."""

    def __init__(
            self, 
            container, 
            name: str,
            settings, 
            connection_type: str,
            device_type: str,
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
        self.connection_type = connection_type
        self.device_type = device_type
        self.get_devices = get_devices
        self.connect_device = connect_device
        self.disconnect_device = disconnect_device
        self.options = {'sticky': 'w', 'padx':10, 'pady':5} # widget placement options
        self.refresh_interval = 2000 # poll rate for finding available devices (ms)

        # Local variables
        self.available_devices = []
        self.selected_device_name = tk.StringVar(value='')
        self.connection_state = False # connection state flag
        self.connected_device = None
        self.connected_device_name = None
        self.default_device = self.default_device_var.get()

        # Configure grid
        self.columnconfigure(0, weight=3)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=0) # scrollbar
        self.rowconfigure(2, weight=1) # treeview and scrollbar

        self._create_widgets()
        self.bind('<Destroy>', self._on_destroy)
        self._refresh_devices_list()

        # Manage command from global connect
        self.running_status.trace_add('write', self._on_running_status_change)

    def _create_widgets(self):
        # Available devices list
        self.devices_label = ttk.Label(self, text=f'{self.connection_type} {self.device_type}s:')
        self.devices_label.grid(column=0, row=0, **self.options)

        # Set default device button
        self.set_default_button = ttk.Button(
            self, text=f'Set as Default {self.device_type}', 
            state='normal', 
            command=self._on_set_default
            )
        self.set_default_button.grid(column=1, row=0, sticky='e', padx=0, pady=5)

        # Devices list
        self.devices_list = ttk.Treeview(
            self, 
            columns=('device','status'), 
            show='headings', 
            height=6, 
            selectmode='browse'
            )
        self.devices_list.heading('device', text=f'{self.device_type} Name', anchor='w')
        self.devices_list.column('device', anchor='w', minwidth=100, stretch=True)
        self.devices_list.heading('status', text='Connection', anchor='w')
        self.devices_list.column('status', anchor='w', minwidth=20, stretch=True)
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

    def _set_status(self, state: bool):
        """Sets connection status label and button states."""
        connection = self.connection_state = state
        if connection:
            self.devices_list.config(selectmode='none')
        else:
            self.devices_list.config(selectmode='browse')
            self.connected_device = None
            self.connected_device_name = None
            
    def _on_device_select(self, event=None):
        """Captures selected item name and updates set default button state."""
        selected_items = self.devices_list.selection()
        if not selected_items:
            self.selected_device_name.set('')
            return

        # Full device name (iid)
        selected_item = selected_items[0] 

        # Disable Set Default button if no devices or default already selected
        if selected_item and selected_item != self.default_device:
            self.set_default_button.config(state='normal')
        else:
            self.set_default_button.config(state='disabled')

        # Make unavailable items non-selectable
        tags = self.devices_list.item(selected_item, 'tags')
        if 'unavailable' in tags:
            self.devices_list.selection_remove(selected_item)
            self.selected_device_name.set('')
            return

        self.selected_device_name.set(selected_item)

    def _on_set_default(self):
        """Makes the selected MIDI output device the new default device."""
        selected_item = self.selected_device_name.get()

        if not selected_item:
            return
        self.default_device = selected_item # update local setting
        self.default_device_var.set(selected_item) # update global setting
        self._refresh_devices_list()

    def _on_running_status_change(self, *args):
        running = self.running_status.get()
        if running:
            self._connect_device()
        else:
            self._disconnect_device()

    def _connect_device(self):
        """Opens connection with selected device."""
        selected_device_name = self.selected_device_name.get()

        # Check if already connected
        if self.connection_status_var.get():
            return

        # Connect to selected device
        self.connected_device_name = selected_device_name
        self.connected_device = self.connect_device(self) # call connect function

        self._set_status(True) # update local setting
        self.connection_var.set(selected_device_name) # update global settings
        self.connection_name_var.set(str(selected_device_name).removesuffix('.' + self.settings.ws_address))
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
            selected_device = self.selected_device_name.get()

            # List focus priority: connected -> selected -> default
            if self.connection_state:
                focus_name = self.connected_device_name
            elif selected_device:
                focus_name = selected_device
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
                tags = self.devices_list.item(focus_item, 'tags')
                if 'unavailable' in tags:
                    self.devices_list.selection_remove(focus_item)
                    self.selected_device_name.set('')
                else:
                    self.devices_list.selection_set(focus_item)
                    self.devices_list.focus(focus_item)
                    self.devices_list.see(focus_item)
                    self.selected_device_name.set(str(focus_name))

    def _refresh_devices_list(self):
        """Clears devices list and rescans for available devices."""
        # Pause refresh while running
        running = self.running_status.get()
        if running:
            return

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

            # Tag default connection
            if connection == self.default_device_var.get():
                connection_name = connection.removesuffix('._websocket._tcp.local.') + ' (default)'  
            else:
                connection_name = connection.removesuffix('._websocket._tcp.local.')
                
            if connection == self.connected_device_name:
                self.devices_list.insert(
                    '', 
                    tk.END, 
                    iid=connection,
                    values=(connection_name, 'Connected'), 
                    tags=('connected',))
            else:
                self.devices_list.insert(
                    '', 
                    tk.END, 
                    iid=connection,
                    values=(connection_name, 'Available'), 
                    tags=('unconnected',))

        # If default device unavailable, flag in list
        if self.default_device and self.default_device not in self.available_devices:
            self.devices_list.insert(
                '', 
                tk.END, 
                iid=self.default_device,
                values=(self.default_device.removesuffix('._websocket._tcp.local.') + ' (default)', 'Unavailable'), 
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


# Callable functions for DeviceFrame
def get_devices(self) -> list[str]:
    """Returns a list of items discovered by Zeroconf listener."""
    available_devices = self.listener.get_available_devices()

    return available_devices

def connect_device(self) -> object:
        """Connects to the selected websocket device on a background thread."""
        device = self.selected_device_name.get()
        connected_device = self.listener.discovered_services.get(device)
        self.connected_device_name = device

        def _run():
            """Catches a failed connection and passes ack out of the thread."""
            try:
                self.listener.connect_to_service(device)
            except Exception as exc:
                print(f'Failed to connect to {device}: {exc}') # DEBUG
                self.after(0, lambda: self._on_connect_failed(device, exc))

        self._connect_thread = threading.Thread(target=_run, daemon=True)
        self._connect_thread.start()
        self._refresh_devices_list()
        print('Device connected:', connected_device, '\n') # DEBUG

        return connected_device

def disconnect_device(self) -> None:
    """Disconnects device and stops background connection thread."""
    print('Device disconnected:', self.listener, '\n') # DEBUG
    self.listener.disconnect()

class DeviceFrame(ConfigFrame):
    """GUI frame for configuring input device connections via Websockets."""
    def __init__(self, container, settings: Settings, listener: WebsocketServiceListener):

        # Pointers to global settings
        self.settings = settings
        self.ws_address: str = self.settings.ws_address
        self.sensors: list[str] = self.settings.sensors

        # Local constants
        self.listener = listener

        # Zeroconf listener records available devices
        self.zeroconf = Zeroconf() 
        self.browser = ServiceBrowser(self.zeroconf, self.ws_address, self.listener)

        # Device connection thread
        self._connect_thread = None

        super().__init__(
            container, 
            'Connect Device',
            settings, 
            'Input',
            'Device', 
            get_devices,
            connect_device, 
            disconnect_device,
            settings.default_device,
            settings.input_connection,
            settings.input_connection_name,
            settings.input_connection_status,
            disconnected_label=settings.input_disconnected_label
        )

    def _on_unexpected_disconnect(self):
        """ Called when the connection drops without the user disconnecting. """
        if not self.connection_state:
            return  # already disconnected normally

        self._set_status(False)
        self.connection_var.set('')
        self.connection_name_var.set(str(self.disconnected_label))
        self.connection_status_var.set(False)
        self._refresh_devices_list()

    def _on_destroy(self, event):
        """ Adds zeroconf cleanup before closing. """
        super()._on_destroy(event)
        if event.widget is self:
            self.browser.cancel()
            self.zeroconf.close()


# Callable functions for MidiFrame
def get_ports(self) -> list[str]:
    """Returns a list of available MIDI output ports using mido/rtmidi."""
    with self.settings.midi_port_lock: # guard thread port access
        try:
            return md.get_output_names() # type: ignore
        except Exception as e:
            print(f"Error scanning MIDI ports via mido: {e}")
            return []

def connect_port(self) -> object:
    """Opens connection with selected MIDI output port."""
    port_name: str = self.connected_device_name
    midi_out: MidiOut = self.midi_out
    midi_out.open_outport(port_name)

    print('MIDI connected:', midi_out._outport, '\n') # DEBUG
    return midi_out

def disconnect_port(self) -> None:
    """Resets active MIDI notes/controllers and closes the MidiOut instance."""
    midi_out: MidiOut = self.connected_device

    if midi_out and hasattr(midi_out, '_outport'):
        print('MIDI disconnected:', midi_out._outport, '\n') # DEBUG

        # Kill all notes and reset control parameters to a neutral position
        midi_out.reset_all()

        midi_out.close_outport()

class MidiFrame(ConfigFrame):
    """GUI frame for configuring MIDI connections."""
    def __init__(self, container, settings: Settings, midi_out: MidiOut):
        super().__init__(
            container, 
            'Midi Settings', 
            settings,
            'MIDI',
            'Port',
            get_ports, 
            connect_port, 
            disconnect_port,
            settings.default_outport,
            settings.output_connection,
            settings.output_connection_name,
            settings.output_connection_status,
            disconnected_label=settings.output_disconnected_label
        )

        self.midi_out = midi_out
        self.settings = settings