import tkinter as tk
from tkinter import ttk

class ControlsFrame(ttk.Frame):
    def __init__(self, container, settings):
        super().__init__(container)

        # Pointers to global settings
        self.settings = settings
        self.default_patch = self.settings.default_patch
        self.loaded_patch = self.settings.loaded_patch

        # Local constants
        self.name = 'Controls'
        self.options = {'sticky':'w', 'padx':10, 'pady':(10, 5)} # widgit placement options

        # Local variables
        self.patch_changed = tk.BooleanVar(value=False)

        # Configure columns
        for i in range(0, 3):
            self.columnconfigure(i, weight=1)

        self._create_widgets()

        # Manage save patch button state
        self.patch_changed.trace_add('write', self._update_save_patch_button_state)
    
    def _create_widgets(self):
        # Patch info
        self.patch_name_label = ttk.Label(self, text='Active patch:')
        self.patch_name_label.grid(column=0, row=0, **self.options)
        self.patch_name = ttk.Label(self, textvariable=self.loaded_patch)
        self.patch_name.grid(column=1, row=0, sticky='ew', padx=10, pady=(10, 5))
        self.save_patch_button = ttk.Button(self, text='Save Patch', state='disabled', command=self._on_save_patch_button)
        self.save_patch_button.grid(column=2, row=0, sticky='e', padx=10, pady=(10, 5))

        # Separate patch info from control mapping
        self.seperator = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.seperator.grid(column=0, row=1, columnspan=3, sticky='ew', padx=10, pady=(10, 5))

        # Control mapping

    def _update_save_patch_button_state(self, *args):
        """Disables save patch button if no changes have been made."""
        if self.patch_changed.get():
            self.save_patch_button.config(state='normal')
        else:
            self.save_patch_button.config(state='disabled')

    def _on_save_patch_button(self):
        pass