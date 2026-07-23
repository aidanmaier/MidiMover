import tkinter as tk
from tkinter import ttk
from gui.status import StatusBar
from gui.input_alt import ConnectionFrame
from gui.mapping import MappingFrame
from gui.output import MidiFrame

class Settings:
    """ Shared config for global settings. """
    # Settings object passed to all gui components so all variables are settable
    # tk variables refire when updated
    def __init__(self):
        # Input constants
        self.ws_address = '_websocket._tcp.local.'
        self.sensors = ['rotation_vector', 'linear_acceleration']

        # Saved settings
        self.sample_rate = tk.IntVar(value=50)
        self.default_device = tk.StringVar(value="Aidan's A54")
        self.default_outport = tk.StringVar(value="IAC Driver Bus 1") # 'IAC Driver Bus 1'

        # Runtime variables
        self.running_status = tk.BooleanVar(value=False)
        self.connection_status = tk.StringVar(value='Unconnected')
        self.input_connection = tk.StringVar(value="< Connect Device >")
        self.input_connection_status = tk.BooleanVar(value=False)
        self.output_connection = tk.StringVar(value='< Connect MIDI Port >')
        self.output_connection_status = tk.BooleanVar(value=False)

class Tabs(ttk.Notebook):
    """ Tabbed container for GUI frames. """

    def __init__(self, container, settings):
        super().__init__(container)
        self.settings = settings
        self.midi_frame = None

        self._create_widgets()
        self.bind('<<NotebookTabChanged>>', self._on_tab_changed)
    
    def _create_widgets(self):
        connection_frame = ConnectionFrame(self, self.settings)
        mapping_frame = MappingFrame(self, self.settings)
        self.midi_frame = MidiFrame(self, self.settings)
        
        for frame in [connection_frame, mapping_frame, self.midi_frame]:
            self.add(frame, text=frame.name)
    
    def _on_tab_changed(self, event):
        """ Force update of new tab for instant rendering. """
        selected_tab = self.select()
        if selected_tab:
            tab = self.nametowidget(selected_tab)
            tab.update_idletasks()

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.settings = Settings()

        # Configure root window
        self.title('Motion Controller')

        # Center window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 600
        window_height = 400
        offset_x = int(screen_width/2 - window_width/2) # distance to screen center - distance to window center
        offset_y = int(screen_height/2 - window_height/2)         

        # Window size
        self.geometry(f'{window_width}x{window_height}+{offset_x}+{offset_y}')
        self.resizable(False, False)
        self.attributes('-topmost', 1) # always on top

        self._create_widgets()
        self.protocol('WM_DELETE_WINDOW', self._on_close)
    
    def _create_widgets(self):
        self.status = StatusBar(self, self.settings)
        self.status.pack(padx=10, fill='x', expand=True)
        self.tabs = Tabs(self, self.settings)
        self.tabs.pack(pady=10, fill='both', expand=True)

    def _on_close(self):
        """ Cleanup handler before window closes. """
        # Close any open midi port
        if self.tabs.midi_frame and self.tabs.midi_frame.connection_state:
            self.tabs.midi_frame._disconnect_outport()
        # Stop stream
        if self.settings.running_status.get():
            self.settings.running_status.set(False)
        self.destroy()


if __name__ == '__main__':
    app = App()
    app.mainloop()
