import mido as md # type supressions needed for Backend methods
from gui.config_frame import ConfigFrame

# Callable functions
def get_ports(self) -> list:
    """ Returns a list of available MIDI ouput ports. """
    available_outports = md.get_output_names() # type: ignore
    return available_outports

def connect_port(self) -> object:
    """ Opens connection with selected MIDI output port. """
    port_name = self.connected_device_name
    connected_outport = md.open_output(port_name) # type: ignore
    return connected_outport

def disconnect_port(self) -> None:
    """ Resets then closes active MIDI output port. """
    port = self.connected_device
    port.reset() # type: ignore # all notes off and reset all controllers
    port.close() # type: ignore

class MidiFrame(ConfigFrame):
    """ GUI frame for configuring MIDI connections. """
    def __init__(self, container, settings):
        super().__init__(
            container, 
            'Midi Settings', 
            settings,
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