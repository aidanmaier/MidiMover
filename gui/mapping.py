import tkinter as tk
from tkinter import ttk

class MappingFrame(ttk.Frame):
    def __init__(self, container, settings):
        super().__init__(container)
        self.settings = settings
        self.name = 'Control Mapping'

        self._create_widgets()
    
    def _create_widgets(self):
        pass