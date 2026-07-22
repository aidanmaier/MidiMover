import tkinter as tk
from tkinter import ttk

from gui_components.input import ConnectionFrame
from gui_components.mapping import MappingFrame
from gui_components.output import MidiFrame

class Settings:
    """ Shared config for global settings. """

    def __init__(self):
        # Input variables
        self.ws_address = '_websocket._tcp.local.'
        self.sensors = ['rotation_vector', 'linear_acceleration']
        self.sample_rate = 50
        
        # Output variables
        self.default_outport = 'IAC Driver Bus 1'
        # self.default_outport = 'Fake Port'
    
    def _set_sample_rate(self, value: int) -> None:
        """ Setter for sample rate value. """
        self.sample_rate = value

class Tabs(ttk.Notebook):
    """ Tabbed container for GUI frames. """
    def __init__(self, container, settings):
        super().__init__(container)
        self.settings = settings

        self._create_widgets()
        self.bind('<<NotebookTabChanged>>', self._on_tab_changed)
    
    def _create_widgets(self):
        for frame in [
            ConnectionFrame(self, self.settings), 
            MappingFrame(self, self.settings), 
            MidiFrame(self, self.settings)
        ]:
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
    
    def _create_widgets(self):
        Tabs(self, self.settings).pack(pady=10, fill='both', expand=True)


if __name__ == '__main__':
    app = App()
    app.mainloop()
