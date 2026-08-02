import mido as md # type supressions needed for Backend methods
import pygame.midi
from threading import Lock
from output import MidiOut
from gui.config_frame import ConfigFrame

MIDI_LOCK = Lock()

# Callable functions
def get_ports(self) -> list:
    """Returns a list of available MIDI ouput ports."""
    with MIDI_LOCK:
        try:
            # Force Pygame MIDI to re-scan hardware ports on macOS
            if pygame.midi.get_init():
                pygame.midi.quit()
            pygame.midi.init()
            return md.get_output_names() # type: ignore
        except Exception as e:
            print(f"Error scanning MIDI ports via Pygame: {e}")
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

        # Reset all MIDI control parameters to a neutral position
        for control_num in range(128):
            msg = md.Message(
                'control_change', 
                channel=midi_out.channel, 
                control=control_num, 
                value=64
                )
            midi_out._outport.send(msg)

        # Clean up active notes/controllers on underlying mido port before closing
        midi_out._outport.reset() # type: ignore

        midi_out.close_outport()

class MidiFrame(ConfigFrame):
    """GUI frame for configuring MIDI connections."""
    def __init__(self, container, settings, midi_out: MidiOut):
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