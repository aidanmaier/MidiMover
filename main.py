import tkinter as tk
from tkinter import ttk
from gui.settings import Settings
from gui.header_frame import Header
from gui.controls_frame import ControlsFrame
from gui.connections_frame import ConnectionsFrame

class Tabs(ttk.Notebook):
    """ Tabbed container for GUI frames. """

    def __init__(self, container, settings):
        super().__init__(container)
        self.settings = settings

        self._create_widgets()
        self.bind('<<NotebookTabChanged>>', self._on_tab_changed)
    
    def _create_widgets(self):
        self.controls = ControlsFrame(self, self.settings)
        self.connections = ConnectionsFrame(self, self.settings)
        
        for frame in [self.controls, self.connections]:
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
        self.tabs_visible = self.settings.tabs_visible

        # Configure root window
        self.title('MidiMotion')

        # Center window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 600
        window_height = 620
        offset_x = int(screen_width/2 - window_width/2) # distance to screen center - distance to window center
        offset_y = int(screen_height/2 - window_height/2)         

        # Window size
        self.geometry(f'{window_width}x{window_height}+{offset_x}+{offset_y}')
        self.resizable(False, False)
        self.attributes('-topmost', 1) # always on top

        self._create_widgets()
        self.tabs.select(0) # Default tab = Controls
        self.protocol('WM_DELETE_WINDOW', self._on_close)

        # Handle toggle button state (in header)
        self.tabs_visible.trace_add('write', self._on_toggle_button)
    
    def _create_widgets(self):
        # Quick config
        self.status = Header(self, self.settings)
        self.status.pack(padx=10, pady=10, fill='x', expand=False)

        # Details tabs
        self.tabs = Tabs(self, self.settings)
        self.tabs.pack(pady=10, fill='both', expand=True)

    def _on_toggle_button(self, *args):
        """Hides or shows tabs based on toggle state."""
        expanded = self.tabs_visible.get()
        if not expanded:
            self.tabs.pack_forget() # does not detroy object so states are not lost
            self.geometry('600x120') # collapse window height
        else:
            self.tabs.pack(padx=10, pady=(0, 10), fill='both', expand=True)
            self.geometry('600x620') # restore window height 

    def _on_close(self):
        """ Cleanup handler before window closes. """
        # Close any open connections
        self.tabs.connections.device_frame._disconnect_device()
        self.tabs.connections.midi_frame._disconnect_device()

        # Stop stream
        if self.settings.running_status.get():
            self.settings.running_status.set(False)
        self.destroy()


if __name__ == '__main__':
    app = App()
    app.mainloop()
