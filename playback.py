import pandas as pd

class DataLoader():
    def __init__(self, directory: str, filename: str) -> None:
        """
        Loads captured motion sensor data from .csv to df
        """
        self.dir = directory
        self.file = filename
        self.filepath = directory + filename

        # Load data to df from .csv
        df = pd.read_csv(self.filepath, header=[0, 1], index_col=0)
        self.data = df

        self.length = df.index[-1] - df.index[0] # length in seconds
        self.samples = len(df.index) # number of samples
        self.polling_rate = self.samples / self.length # in Hz

    def stream(self, sensor: str, axis: str) -> list:
        """
        Returns data for given sensor and axis as list
        """
        data = self.data[(sensor, axis)]
        return list(data)


    
