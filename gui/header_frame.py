import tkinter as tk
from tkinter import ttk

class Header(ttk.Frame):
    """Top-level status bar showing connection status."""

    def __init__(self, container, settings):
        super().__init__(container)

        # Pointers to global settings
        self.settings = settings
        self.input_settings = {
             'connection_name': self.settings.input_connection_name,
             'connection_status': self.settings.input_connection_status,
             'disconnected_label': self.settings.input_disconnected_label,
        }
        self.output_settings = {
             'connection_name': self.settings.output_connection_name,
             'connection_status': self.settings.output_connection_status,
             'disconnected_label': self.settings.output_disconnected_label             
        }
        self.default_patch = self.settings.default_patch
        self.loaded_patch = self.settings.loaded_patch

        # Local constants
        self.name = 'Quick Configuration'
        self.options = {'sticky':'w', 'padx':10, 'pady':(10, 5)} # widgit placement options
        self.new_patch_label = '< New patch >'

        # Local variables
        self.ready_state = tk.StringVar(value='Unconnected')
        
        # TODO: replace with real pacth names/source once available
        self.patch_names = [
            self.new_patch_label, # Always present and first item in list
            'patch 1', 
            self.default_patch.get(), 
            'patch 2'
            ]
        self.patch_var = tk.StringVar(value=self.patch_names[0])
        
        # Configure grid
        self.columnconfigure(0, weight=2)
        for i in range(1, 5):
            self.columnconfigure(i, weight=1)

        for i in range(2):
            self.rowconfigure(i, weight=1)

        self._create_widgets()

        # Auto-load default patch if any, otherwise load new patch
        self._initiate_menu()
        self._on_load_patch_button()

        # Keep output status colors in sync with connection state
        self._create_status_tracer(self.input_settings['connection_name'], self.input_status_label, **self.input_settings)
        self._create_status_tracer(self.input_settings['connection_status'], self.input_status_label, **self.input_settings)
        self._update_status(self.input_status_label, **self.input_settings)
    
        self._create_status_tracer(self.output_settings['connection_status'], self.output_status_label, **self.output_settings)
        self._create_status_tracer(self.output_settings['connection_name'], self.output_status_label, **self.output_settings)
        self._update_status(self.output_status_label, **self.output_settings)

        # Manage start button state
        self.settings.input_connection.trace_add('write', self._update_start_button_state)
        self.settings.output_connection.trace_add('write', self._update_start_button_state)
        self.settings.running_status.trace_add('write', self._update_start_button_state)
        self._update_start_button_state()

        # Manage patch button states
        self.patch_var.trace_add('write', self._update_patch_buttons_state)
        self._update_patch_buttons_state()

    def _create_widgets(self):
        # Start/Stop button, status icon and label
        self.ready_frame = ttk.Frame(self)
        self.ready_frame.grid(column=0, row=0, sticky='w', padx=0, pady=0)

        self.status_icon = tk.Canvas(self.ready_frame, width=14, height=14, highlightthickness=0)
        self.status_icon_id = self.status_icon.create_oval(2, 2, 12, 12, fill='red', outline='')
        self.status_icon.grid(column=0, row=0, **self.options)

        self.ready_label = ttk.Label(self.ready_frame, textvariable=self.ready_state)
        self.ready_label.grid(column=1, row=0, sticky='w', padx=(0, 10), pady=(10, 5))

        self.start_button = ttk.Button(self, text='START', command=self._on_start_button)
        self.start_button.grid(column=0, row=1, **self.options)

        # Input information
        self.input_label = ttk.Label(self, text='Device:')
        self.input_label.grid(column=1, row=0, **self.options)
        self.input_status_label = ttk.Label(self, textvariable=self.settings.input_connection_name)
        self.input_status_label.grid(column=2, row=0, **self.options)

        # Output information
        self.output_label = ttk.Label(self, text='MIDI Port:')
        self.output_label.grid(column=3, row=0, **self.options)
        self.output_status_label = ttk.Label(self, textvariable=self.settings.output_connection_name)
        self.output_status_label.grid(column=4, row=0, **self.options)

        # Load patchs
        self.patch_menu = ttk.OptionMenu(
            self,
            self.patch_var,
            self.patch_names[0],
            *self.patch_names
            )
        self.patch_menu.grid(column=1, row=1, columnspan=2, sticky='ew', padx=10, pady=(10, 5))

        self.load_patch_button = ttk.Button(self, text='Load', command=self._on_load_patch_button)
        self.load_patch_button.grid(column=3, row=1, **self.options)
        self.patch_info_button = ttk.Button(self, text='Info', command=self._on_patch_info_button)
        self.patch_info_button.grid(column=4, row=1, **self.options)

    def _create_status_tracer(self, variable: tk.Variable, label: ttk.Label, **global_settings) -> None:
            """Creates a global variable tracer assigns it to a label, and passes it a Dict of arguments"""
            variable.trace_add(
                'write',
                lambda *args: self._update_status(status_label=label, **global_settings)
            )
         
    def _update_status(self, status_label: ttk.Label, connection_name: tk.StringVar, connection_status: tk.BooleanVar, disconnected_label: str) -> None:
        """Updates connection status label with correct color."""
        name = connection_name.get()
        if name == disconnected_label: # no default or connected device available
            color = 'red'
        elif connection_status.get(): # device connected
            color = 'green'
        else:
            color = 'blue' # default device available but unconnected
        status_label.config(foreground=color, text=name)

    def _update_start_button_state(self, *args):
        """ Enables start button only if both inputs connected or have available defaults """
        input_connection = self.settings.input_connection.get()
        output_connection = self.settings.output_connection.get()
        ready = bool(input_connection) and bool(output_connection)
        running = self.settings.running_status.get()

        # Set status icon color
        if running:
            icon_color = 'green'
            self.ready_state.set('Connected')
        elif ready:
            icon_color = 'blue'
            self.ready_state.set('Ready')
        else:
            icon_color = 'red'
            self.ready_state.set('Unconnected')

        self.status_icon.itemconfig(self.status_icon_id, fill=icon_color)

        if ready: 
            self.start_button.config(state='normal')
        else:
            self.start_button.config(state='disabled')

            # Reset state on disconnect
            if running:
                self.settings.running_status.set(False)
                self.start_button.config(text='START')
                return

    def _update_patch_buttons_state(self, *args):
        """Disables patch Load and Info buttons if selected patch is already loaded."""
        selected_patch = self.patch_var.get()
        if selected_patch == self.loaded_patch.get():
            self.load_patch_button.config(state='disabled')
            self.patch_info_button.config(state='disabled')
        else:
            self.load_patch_button.config(state='normal')
            self.patch_info_button.config(state='normal')

        # Cannot read info about a new patch
        if selected_patch == self.new_patch_label:
            self.patch_info_button.config(state='disabled')

    def _initiate_menu(self):
        """Set initial menu selection to the default patch, or new patch if no default."""
        default_patch = self.default_patch.get()
        if default_patch:
            self.patch_var.set(default_patch)
        else:
            self.patch_var.set(self.new_patch_label)

    def _on_start_button(self):
        running = self.settings.running_status.get()
        if not running:
            self.settings.running_status.set(True)
            self.start_button.config(text='STOP')
        else:
            self.settings.running_status.set(False)
            self.start_button.config(text='START')

    def _on_load_patch_button(self):
        """Loads the patch selected in the patch menu."""
        # TODO: patch loading logic
        patch = self.patch_var.get()
        self.loaded_patch.set(patch)
        self._update_patch_buttons_state()

    def _on_patch_info_button(self):
        pass


            

