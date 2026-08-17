from tkinter import ttk
from gui.controls_frame import ControlsFrame
from gui.connections_frame import ConnectionsFrame
from input import WebsocketServiceListener
from output import MidiOut

class Tabs(ttk.Frame):
    """Container for Controls and Connections GUI frames."""

    def __init__(self, container, settings, listener: WebsocketServiceListener, midi_out: MidiOut):
        super().__init__(container)
        self.settings = settings
        self.listener = listener
        self.midi_out = midi_out

        # Active frame state
        self.active_frame = None

        self._create_widgets()
    
    def _create_widgets(self):
        self.controls = ControlsFrame(self, self.settings)
        self.connections = ConnectionsFrame(self, self.settings, self.listener, self.midi_out) # pass listener and midi_out to gui

    def show_frame(self, target_frame: ttk.Frame):
        """Shows the target frame and hides the active frame, or hides all frames."""
        # Hide all frames if click of the active frame
        if self.active_frame == target_frame:
            self.hide_all_frames()
            return False

        # Else, hide active frame
        if self.active_frame:
            self.active_frame.pack_forget()

        # Show target frame
        target_frame.pack(fill='both', expand=True)
        self.active_frame = target_frame
        target_frame.update_idletasks()
        return True

    def hide_all_frames(self):
        """Hides both frames."""
        if self.active_frame:
            self.active_frame.pack_forget()
            self.active_frame= None