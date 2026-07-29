import asyncio
import threading
import time
import tkinter as tk
from tkinter import ttk
from pathlib import Path
from settings import Settings
from gui.header_frame import Header
from gui.controls_frame import ControlsFrame
from gui.connections_frame import ConnectionsFrame
from input import WebsocketServiceListener, DataStreamer
from player import Player

# Filepaths
BASE_DIR = Path(__file__).resolve().parent
DATA_FOLDER = BASE_DIR / "app_data"
SETTINGS_FILEPATH = DATA_FOLDER / "settings.json"
PATCHES_FILEPATH = DATA_FOLDER / "patches.json"

# Callback function
def print_sample(sample):
    print(sample)

class Tabs(ttk.Notebook):
    """ Tabbed container for GUI frames. """

    def __init__(self, container, settings, listener):
        super().__init__(container)
        self.settings = settings
        self.listener: WebsocketServiceListener = listener

        self._create_widgets()
        self.bind('<<NotebookTabChanged>>', self._on_tab_changed)
    
    def _create_widgets(self):
        self.controls = ControlsFrame(self, self.settings)
        self.connections = ConnectionsFrame(self, self.settings, self.listener)
        
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

        #Pointers to global settings
        self.settings = Settings(SETTINGS_FILEPATH, PATCHES_FILEPATH)
        self.tabs_visible: tk.BooleanVar = self.settings.tabs_visible
        self.running_status: tk.BooleanVar = self.settings.running_status
        self.sensors: list[str] = self.settings.sensors
        self.sample_rate: tk.IntVar = self.settings.sample_rate

        # Configure root window
        self.title('MidiMotion')

        # Center window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 600
        window_height = 620
        offset_x = (screen_width - window_width) // 2 # distance to screen center - distance to window center
        offset_y = (screen_height - window_height) // 2         

        # Window size
        self.geometry(f'{window_width}x{window_height}+{offset_x}+{offset_y}')
        self.resizable(False, False)
        self.attributes('-topmost', 1) # always on top

        # Background thread for async loop, as async not supported by tkinter
        self._run_loop = asyncio.new_event_loop()
        self._run_loop_thread = threading.Thread(target=self._run_loop.run_forever, daemon=True)
        self._run_loop_thread.start()
        self._stop_event = None
        self._stream_future = None

        self.listener = WebsocketServiceListener(
            self.settings.sensors,
            on_disconnect=lambda: self.after(0, self._on_listener_disconnect)
        )
        self.data_streamer = DataStreamer(self.listener)

        self._create_widgets()
        self.tabs.select(0) # Default tab = Controls
        self.protocol('WM_DELETE_WINDOW', self._on_close) # Handle window close

        # Handle toggle button state (in header)
        self.tabs_visible.trace_add('write', self._on_toggle_button)

        # Handle running status
        self.running_status.trace_add('write', self._on_running_status_change)
    
    def _create_widgets(self):
        # Quick config
        self.header = Header(self, self.settings)
        self.header.pack(padx=10, pady=10, fill='x', expand=False)

        # Details tabs
        self.tabs = Tabs(self, self.settings, self.listener)
        self.tabs.pack(pady=10, fill='both', expand=True)

    def _on_listener_disconnect(self):
        """Stops the running status if the websocket closes unexpectedly."""
        if self.running_status.get():
            self.running_status.set(False)

            # Reset GUI
            self.tabs.connections.device_frame._on_unexpected_disconnect()
            self.header.start_button.config(state='disable', text='START')

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

    def _threadsafe_callback(self, func):
        """Threadsafe wrapper for the callback function."""
        def wrapper(sample):
            self.after(0, func, sample)
        return wrapper

    def _on_running_status_change(self, *args):
        """Start/stop data stream on status change."""
        running = self.running_status.get()

        if running:
            self._wait_for_listener_and_start(start_time=time.time())
        else:
            if self._stop_event is not None:
                self._run_loop.call_soon_threadsafe(self._stop_event.set)

    def _wait_for_listener_and_start(self, start_time: float, timeout=5.0):
        """In background thread, wait for listener to connect, then run stream. Timeout after 50s."""
        # Check if status was canceled while waiting
        if not self.running_status.get():
            return

        if self.listener.open:
            # Successfully connected — start streaming
            self._stop_event = asyncio.Event()
            coro = self.data_streamer.stream(
                self._threadsafe_callback(Player.play), # callback function to play midi from data
                self.sample_rate.get(),
                stop_event=self._stop_event
            )
            self._stream_future = asyncio.run_coroutine_threadsafe(coro, self._run_loop)
        elif time.time() - start_time > timeout:
            # Timed out — safely revert button/state
            self.running_status.set(False)
            print("Timeout Error: Websocket listener failed to open in time.")
        else:
            # Re-check after 50ms
            self.after(50, lambda: self._wait_for_listener_and_start(start_time, timeout))


if __name__ == '__main__':
    app = App()
    app.mainloop()
