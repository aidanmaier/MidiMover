import os
import asyncio
import threading
import time
import mido
import sys
import tkinter as tk
from tkinter import ttk
from pathlib import Path

from settings import Settings
from gui.tabs_frame import Tabs
from gui.header_frame import Header
from input import WebsocketServiceListener, DataStreamer
from output import MidiOut, MidiPlayer

# Configure Mido rtmidi backend to use CoreMIDI engine on macOS
# to avoid python-rtmidi PyEval_RestoreThread GIL assertion failure
def configure_mido_backend():
    if sys.platform == "darwin": # macOS
        try:
            os.environ["RTMIDI_API"] = "MACOSX_CORE"  # force CoreMIDI driver
            mido.set_backend('mido.backends.rtmidi')  
            print("mido: Configured 'rtmidi' with native CoreMIDI backend for macOS.")
        except Exception as e:
            print(f"mido: Failed to load rtmidi backend ({e}). Falling back to default.")
    else: # Windows / Linux
        try:
            mido.set_backend('mido.backends.rtmidi')
            print("mido: Configured 'rtmidi' backend.")
        except Exception as e:
            print(f"mido: Falling back to default backend ({e}).")
configure_mido_backend()

# Filepaths
BASE_DIR = Path(__file__).resolve().parent
DATA_FOLDER = BASE_DIR / "app_data"
SETTINGS_FILEPATH = DATA_FOLDER / "settings.json"
PATCHES_FILEPATH = DATA_FOLDER / "patches.json"

class App(tk.Tk):
    def __init__(self):

        super().__init__()

        #Pointers to global settings
        self.settings = Settings(SETTINGS_FILEPATH, PATCHES_FILEPATH)
        self.running_status: tk.BooleanVar = self.settings.running_status
        self.sensors: list[str] = self.settings.sensors
        self.sample_rate: tk.IntVar = self.settings.sample_rate

        # Configure root window
        self.title('MidiMover')

        # Center window
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        self.window_width = 760
        self.window_min_height = 120 # height when config tabs closed
        self.window_max_height = 640 #height when config tabs open
        offset_x = (screen_width - self.window_width) // 2 # distance to screen center - distance to window center
        offset_y = (screen_height - self.window_max_height) // 2         

        # Window size
        self.geometry(f'{self.window_width}x{self.window_min_height}+{offset_x}+{offset_y}')
        self.resizable(False, False)
        self.attributes('-topmost', 1) # always on top

        # Configure widget styling
        self.style = ttk.Style()
        # Use tk theme for clearer disabled buttons
        self.style.theme_use('alt') # tk styles: ('aqua', 'clam', 'alt', 'default', 'classic')
        self._configure_styles()

        # Background thread for async loop, as async not supported by tkinter
        self._run_loop = asyncio.new_event_loop()
        self._run_loop_thread = threading.Thread(target=self._run_loop.run_forever, daemon=True)
        self._run_loop_thread.start()
        self._stop_event = None
        self._stream_future = None

        # Input
        self.listener = WebsocketServiceListener(
            self.settings.sensors,
            on_disconnect=lambda: self.after(0, self._on_listener_disconnect)
        )
        self.data_streamer = DataStreamer(self.listener)

        # Output
        self.midi_out = MidiOut(self.settings)
        self.midi_player = MidiPlayer(self.settings, self.midi_out)

        self._create_widgets()
        self.protocol('WM_DELETE_WINDOW', self._on_close) # Handle window close

        # Handle running status
        self.running_status.trace_add('write', self._on_running_status_change)

        # Start the polling loop on the main Tkinter thread
        self._poll_midi_queue()
    
    def _create_widgets(self):
        # Quick config header
        self.header = Header(self, self.settings)
        self.header.pack(padx=10, pady=10, fill='x', expand=False)

        # Connections and Controls config tabs
        self.tabs = Tabs(self, self.settings, self.listener, self.midi_out) # pass listener and midi_out to gui
        self.tabs.pack(padx=10, pady=10, fill='both', expand=True)

    def _configure_styles(self):
        # Active state for button
        self.style.configure(
            'Active.TButton',
            background='#0078d7',
            foreground='white'
        )

        self.style.map(
            'Active.TButton',
            background=[('disabled', 'light grey'), ('pressed', '#005a9e'), ('active', '#0078d7')],
            foreground=[('disabled', '#a0a0a0'), ('pressed', 'white'), ('active', 'white')]
        )

        # Default style for inactive button
        self.style.configure(
            'Default.TButton',
            foreground='black'
        )
        self.style.map(
            'Default.TButton',
            foreground=[('disabled', '#a0a0a0'), ('pressed', 'black'), ('active', 'black')]
        )

        # Styles for parameter selectors
        style = ttk.Style()
        style.configure('Filled.TCombobox', foreground='green')
        style.configure('Empty.TCombobox', foreground='black', bordercolor='red')

        style.map(
            'Empty.TCombobox',
            bordercolor=[('readonly', 'red'), ('focus', 'red'), ('!focus', 'red')],
            fieldbackground=[('readonly', 'white')],
        )

    def _toggle_tabs(self, panel_name:str):
        """Hides active tab and shows new tab."""
        if panel_name == 'connections':
            target_frame = self.tabs.connections
        else:
            target_frame = self.tabs.controls

        frame_visible = self.tabs.show_frame(target_frame)

        if frame_visible:
            self.header._update_tabs_buttons(panel_name)
            self.geometry(f'{self.window_width}x{self.window_max_height}') # restore
        else:
            self.header._update_tabs_buttons(None)
            self.geometry(f'{self.window_width}x{self.window_min_height}') # minimise

    def _on_listener_disconnect(self):
        """Stops the running status if the websocket closes unexpectedly."""
        if self.running_status.get():
            self.running_status.set(False)

            # Reset GUI
            self.tabs.connections.device_frame._on_unexpected_disconnect()
            self.header.start_button.config(state='disable', text='PLAY', style='Default.TButton')

    def _on_close(self):
        """ Cleanup handler before window closes. """
        # Send full reset to MIDI hardware before exit
        if hasattr(self, 'midi_player'):
            self.midi_player.reset_all()
        
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
            # Stop the async streaming loop
            if self._stop_event is not None:
                self._run_loop.call_soon_threadsafe(self._stop_event.set)
            
            # Reset all MIDI output channels immediately
            if hasattr(self, 'midi_player'):
                self.midi_player.reset_all()

    def _poll_midi_queue(self):
        """ Drain queued MIDI output requests on Tkinter's main thread """
        if hasattr(self, 'midi_player'):
            asyncio.run_coroutine_threadsafe(
                self.midi_player.process_queue(),
                self._run_loop
            )
        
        # Schedule next run in ~10ms (100Hz tick rate)
        self.after(10, self._poll_midi_queue)

    def _wait_for_listener_and_start(self, start_time: float, timeout=5.0):
        """In background thread, wait for listener to connect, then run stream."""
        if not self.running_status.get():
            return

        if self.listener.open:
            self._stop_event = asyncio.Event()
            
            # Successfully connected — start streaming
            coro = self.data_streamer.stream(
                self.midi_player.play, # callback function to play midi from input data
                self.sample_rate.get(),
                stop_event=self._stop_event
            )
            self._stream_future = asyncio.run_coroutine_threadsafe(coro, self._run_loop)
            self._stream_future.add_done_callback(self._on_stream_done)

        elif time.time() - start_time > timeout:
            self.running_status.set(False)
            print("Timeout Error: Websocket listener failed to open in time.")
        else:
            self.after(50, lambda: self._wait_for_listener_and_start(start_time, timeout))

    def _on_stream_done(self, future):
        if future.cancelled():
            return
        exc = future.exception()
        if exc is not None:
            print(f"Streaming task failed: {exc!r}")
            self.after(0, lambda: self.running_status.set(False))


if __name__ == '__main__':
    app = App()
    app.mainloop()



