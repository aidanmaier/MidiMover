import mido as md # type supressions needed for Backend methods
from threading import Lock
from output import MidiOut
from settings import Settings
from gui.config_frame import ConfigFrame
# Callable functions
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

        # Clean up active notes/controllers on underlying mido port before closing
        midi_out._outport.reset() # type: ignore

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