import tkinter as tk
from tkinter import ttk
import json

# Patches filepaths
DATA_FOLDER_FILEPATH = './app_data/'
PATCHES_FILENAME = 'patches.json'
PATCHES_FILEPATH = DATA_FOLDER_FILEPATH + PATCHES_FILENAME

class ControlsFrame(ttk.Frame):
    def __init__(self, container, settings):
        super().__init__(container)

        # Pointers to global settings
        self.settings = settings
        self.default_patch = self.settings.default_patch
        self.loaded_patch_name = self.settings.loaded_patch_name

        # Local constants
        self.name = 'Controls'
        self.options = {'sticky':'w', 'padx':10, 'pady':(10, 5)} # widgit placement options

        # Local variables
        self.patch_changed = tk.BooleanVar(value=False)
        self.loaded_patch_data = None
        self.loaded_patch_description = tk.StringVar(value='')
    
        # Configure columns
        for i in range(0, 3):
            self.columnconfigure(i, weight=1)

        self._create_widgets()

        # Manage save patch button state
        self.patch_changed.trace_add('write', self._update_save_patch_button_state)

        # Manage loaded patch info
        self.loaded_patch_name.trace_add('write', self._update_patch_info)
        self._update_patch_info()
    
    def _create_widgets(self):
        # Patch info
        self.patch_name_label = ttk.Label(self, text='Active patch:', width=14)
        self.patch_name_label.grid(column=0, row=0, **self.options)
        self.patch_name = ttk.Label(self, textvariable=self.loaded_patch_name)
        self.patch_name.grid(column=1, row=0, sticky='w', padx=10, pady=(10, 5))

        self.save_patch_button = ttk.Button(self, text='Save Patch', state='disabled', command=self._on_save_patch_button)
        self.save_patch_button.grid(column=2, row=0, sticky='e', padx=10, pady=(10, 5))

        self.patch_description_label = ttk.Label(self, text='Description:', width=14)
        self.patch_description_label.grid(column=0, row=1, **self.options)
        self.patch_description = ttk.Label(self, textvariable=self.loaded_patch_description)
        self.patch_description.grid(column=1, row=1, columnspan=2, sticky='w', padx=10, pady=(10, 5))

        # Separate patch info from control mapping
        self.seperator = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.seperator.grid(column=0, row=2, columnspan=3, sticky='ew', padx=10, pady=(10, 5))

        # Control mapping
        self.parameters_frame = ttk.Frame(self)
        self.parameters_frame.grid(column=0, row=3, columnspan=3, sticky='ew')

        self.input_mapping_frame = self._build_mapping_frame(0, 'Input')
        self.out_mapping_frame = self._build_mapping_frame(1, 'Output')


        self._update_parameter_list()


    def _update_save_patch_button_state(self, *args) -> None:
        """Disables save patch button if no changes have been made."""
        if self.patch_changed.get():
            self.save_patch_button.config(state='normal')
        else:
            self.save_patch_button.config(state='disabled')

    def _update_patch_info(self, *args) -> None:
        """ Updates loaded patch description and settings when loaded patch name changes"""
        with open(PATCHES_FILEPATH) as INFILE:
            patches_data = json.load(INFILE)
        self.loaded_patch_data = patches_data['patches'][self.loaded_patch_name.get()]
        patch_description = self.loaded_patch_data['description']
        self.loaded_patch_description.set(patch_description)
        self._update_parameter_list()

    def _update_parameter_list(self):
        parameter_data = None
        parameter_list = []

        if self.loaded_patch_data:
            parameter_data = self.loaded_patch_data['parameters']
            parameter_list = parameter_data.keys()
            row_count = 3

            # for parameter in parameter_list:
            #     label = ttk.Label(self.parameters_frame, text=parameter_data[parameter]['properties']['name'])
            #     label.grid(column=1, row=row_count, **self.options)
            #     row_count += 1

    def _build_mapping_frame(self, col, connection):
        frame = ttk.Frame(self.parameters_frame)
        frame.grid(column=col, row=0)

        title = ttk.Label(frame, text=connection)
        title.grid(column=0, row=0, columnspan=2, sticky='ew', padx=10, pady=(0, 5))

        parameter_label = ttk.Label(frame, text='Parameter')
        parameter_label.grid(column=0, row=1, sticky='w', padx=10, pady=(0, 5))

        range_label = ttk.Label(frame, text='Range')
        range_label.grid(column=1, row=1, sticky='w', padx=10, pady=(0, 5))

        self.seperator = ttk.Separator(frame, orient=tk.HORIZONTAL)
        self.seperator.grid(column=0, row=2, columnspan=4, sticky='ew', padx=10, pady=(10, 5))

        return frame

    def _on_save_patch_button(self):
        pass
