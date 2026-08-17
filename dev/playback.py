import time
import asyncio
import pandas as pd
from pathlib import Path
from typing import Callable, Optional
from sys import path
path.insert(0, "../")
from app import App

INPUT_DIR = Path(__file__).resolve().parent / 'test_data'
INPUT_FILENAME = 'test.csv'
LOOP = True # loop playback

class DataLoader():
    def __init__(self, directory: str | Path, filename: str) -> None:
        """Loads captured motion sensor data from .csv into DataFrame."""
        self.dir = Path(directory)
        self.file = filename
        self.filepath = self.dir / filename

        # Load data to df from .csv
        df = pd.read_csv(self.filepath, header=[0, 1], index_col=0)
        self.data = df
        self.sensors = {tup[0] for tup in df.columns}  # Set of available sensors

        self.length = (df.index[-1] - df.index[0]) / 1_000_000_000.0  # Length in seconds
        self.samples = len(df.index)  # Number of samples
        self.sample_rate = (self.samples - 1) / self.length if self.length > 0 else 50.0
        self.sample_period = 1 / self.sample_rate

    def get_sample(self, index: int) -> dict:
        """Returns sample formatted as dictionary expected by MidiPlayer."""
        row = self.data.iloc[index]
        timestamp = self.data.index[index]

        sensors = {}
        for (sensor, _), val in row.items(): # type: ignore
            if sensor not in sensors:
                sensors[sensor] = []
            if pd.notna(val):
                sensors[sensor].append(val)

        return {
            'timestamp': timestamp,
            'sensors': sensors
        }

    async def stream(
        self,
        callback: Callable[[dict], None],
        speed_factor: float = 1.0,
        loop: bool = False,
        stop_event: Optional[asyncio.Event] = None
    ) -> None:
        """Streams loaded data at average recorded rate."""
        if self.samples == 0:
            return

        index = 0
        start_ts = self.data.index[0]
        start_mono = time.monotonic()

        while index < self.samples:
            if stop_event and stop_event.is_set():
                break

            # 1. Trigger callback with current sample
            sample = self.get_sample(index)
            callback(sample)
            index += 1

            # 2. If finished and looping, reset benchmark clock
            if index >= self.samples:
                if loop:
                    index = 0
                    start_ts = self.data.index[0]
                    start_mono = time.monotonic()
                else:
                    break

            # 3. Calculate target sleep duration based on exact recorded timestamp difference
            next_ts = self.data.index[index]
            target_elapsed = ((next_ts - start_ts) / 1_000_000_000.0) / speed_factor
            actual_elapsed = time.monotonic() - start_mono
            delay = target_elapsed - actual_elapsed

            if delay > 0:
                await asyncio.sleep(delay)


class PlaybackApp(App):
    """Development App subclass that plays back sensor data from a .csv file."""

    def __init__(self, input_dir: Path = INPUT_DIR, input_filename: str = INPUT_FILENAME):
        # Load recorded CSV data
        self.data_loader = DataLoader(input_dir, input_filename)

        super().__init__()

        # Update available sensors in settings from loaded dataset
        self.settings.sensors = list(self.data_loader.sensors)

    def _on_running_status_change(self, *args):
        """Starts/stops CSV playback on running status change."""
        running = self.running_status.get()

        if running:
            self._start_playback()
        else:
            # Cancel playback loop thread-safely
            if self._stop_event is not None:
                self._run_loop.call_soon_threadsafe(self._stop_event.set)

            # Silence MIDI notes on stop
            if hasattr(self, 'midi_player'):
                self.midi_player.reset_all()

    def _start_playback(self):
        """Schedules CSV data streaming on the background asyncio loop."""
        self._stop_event = asyncio.Event()

        coro = self.data_loader.stream(
            callback=self.midi_player.play,
            speed_factor=1.0,
            loop=LOOP,
            stop_event=self._stop_event
        )

        self._stream_future = asyncio.run_coroutine_threadsafe(coro, self._run_loop)
        self._stream_future.add_done_callback(self._on_playback_done)

    def _on_playback_done(self, future):
        """Handles completion or errors on stream finish."""
        if future.cancelled():
            return

        exc = future.exception()
        if exc is not None:
            print(f"Playback error: {exc!r}")

        # Reset UI button state back to PLAY when file finishes
        self.after(0, lambda: self.running_status.set(False))


if __name__ == '__main__':
    app = PlaybackApp()
    app.mainloop()