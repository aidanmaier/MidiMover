import os
import pandas as pd
from pathlib import Path
from sys import path
path.insert(0, "../")
from app import App

AXES = ['x', 'y', 'z', 'w']
OUTPUT_DIR = Path(__file__).resolve().parent / 'test_data'
OUTPUT_FILENAME = 'test.csv'

class RecordingApp(App):
    """Development App subclass that records input data to .csv file."""

    def __init__(self):
        super().__init__()

        # Saved data structure
        labels = [self.settings.sensors, AXES]
        self._record_cols = pd.MultiIndex.from_product(labels, names=['Sensor', 'Axis'])
        self._recorded = pd.DataFrame(columns=self._record_cols)

        # Wrap the existing MIDI play callback with recorder
        original_play = self.midi_player.play

        def recording_play(sample):
            self._save_sample(sample)
            original_play(sample)

        self.midi_player.play = recording_play

    def _save_sample(self, sample: dict) -> None:
        """Appends one streamed sample to the in-memory recording buffer."""
        timestamp = sample.get('timestamp')
        if timestamp is None:
            return

        row = pd.Series(index=self._record_cols, dtype=float)
        sensor_data = sample.get('sensors', {})
        for sensor in self.settings.sensors:
            values = sensor_data.get(sensor, [])
            if isinstance(values, (list, tuple)):
                for axis_name, value in zip(AXES, values):
                    row[(sensor, axis_name)] = value

        self._recorded.loc[timestamp, self._record_cols] = row.values

    def _write_csv(self) -> None:
        """Saves the recording buffer to .csv at filepath."""
        if self._recorded.index.empty:
            print('\nNo sensor data was captured.')
            return

        os.makedirs(OUTPUT_DIR, exist_ok=True)
        out_path = OUTPUT_DIR / OUTPUT_FILENAME
        self._recorded.to_csv(out_path)
        print(f'\noutput saved to: {out_path}')

    def _on_close(self):
        """Save the recording before the normal shutdown sequence."""
        self._write_csv()
        super()._on_close()


if __name__ == '__main__':
    app = RecordingApp()
    app.mainloop()


