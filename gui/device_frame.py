import threading
from zeroconf import Zeroconf, ServiceBrowser
from logic.listen import WebsocketServiceListener
from gui.config_frame import ConfigFrame

# Callable functions
def get_devices(self) -> list[str]:
    """ Returns a list of items discovered by Zeroconf listener. """
    available_devices = self.listener.get_available_devices()

    return available_devices

def connect_device(self) -> object:
        """ Connects to the selected websocket device on a background thread. """
        device = self.selected_device_name
        connected_device = self.listener.discovered_services.get(device)
        self.connected_device_name = device

        def _run():
            """Catches a failed connection and passes ack out of the thread."""
            try:
                self.listener.connect_to_service(device)
            except Exception as exc:
                print(f'Failed to connect to {device}: {exc}')
                self.after(0, lambda: self._on_connect_failed(device, exc))

        self._connect_thread = threading.Thread(target=_run, daemon=True)
        self._connect_thread.start()
        self._refresh_devices_list()
        print('Device connected:', connected_device, '\n') # DEBUG

        return connected_device

def disconnect_device(self) -> None:
    """ Disconnects device and stops background connection thread. """
    print('Device disconnected:', self.listener, '\n') # DEBUG
    self.listener.disconnect()
    if self._connect_thread and self._connect_thread.is_alive():
        self._connect_thread.join(timeout=2) # timeout for WS server to respond

class DeviceFrame(ConfigFrame):
    """ GUI frame for configuring input device connections via Websockets. """
    def __init__(self, container, settings):
        self.ws_address = settings.ws_address
        self.sensors = settings.sensors

        # Zeroconf listener records available devices
        self.zeroconf = Zeroconf() 
        self.listener = WebsocketServiceListener(
            self.sensors, 
            # _on_unexpected_disconnect fires if disconnection on device side
            on_disconnect=lambda: self.after(0, self._on_unexpected_disconnect) 
            )
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

        

        
