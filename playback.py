import pandas as pd

class DataLoader():
    def __init__(self, directory: str, filename: str) -> None:
        self.dir = directory
        self.file = filename
        self.filepath = directory + filename

        # Load data to df from .csv
        df = pd.read_csv(self.filepath, header=[0, 1], index_col=0)
        self.data = df

        self.length = df.index[-1] - df.index[0] # length in seconds
        self.samples = len(df.index) # number of samples
        self.polling_rate = self.samples / self.length # in Hz

class SensorStreamer():
    def __init__(self, dataLoader: DataLoader) -> None:
        self._dataLoader = dataLoader
        self.polling_rate = dataLoader.polling_rate

    def stream(self, sensor: str, axis: str) -> list:
        data = self._dataLoader.data[(sensor, axis)]
        return list(data)
