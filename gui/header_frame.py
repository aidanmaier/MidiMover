import tkinter as tk
from tkinter import ttk
from settings import Settings

class Header(ttk.Frame):
    """Quick config header showing connection status and patch loading."""

    def __init__(self, container, settings: Settings):
        super().__init__(container)

        # Pointers to global settings
        self.settings = settings
        self.default_patch: tk.StringVar = self.settings.default_patch
        self.saved_patches_list = [
            f"{patch} (default)" if patch == self.default_patch.get() else patch # tag default patch
            for patch in self.settings.saved_patches_list
        ]
        self.loaded_patch_name: tk.StringVar = self.settings.loaded_patch_name
        self.loaded_patch_description: tk.StringVar = self.settings.loaded_patch_description
        self.loaded_patch_parameters_data: dict = self.settings.loaded_patch_parameters_data
        self.running_status: tk.BooleanVar = self.settings.running_status
        self.selected_input: tk.StringVar = self.settings.selected_input
        self.selected_output: tk.StringVar = self.settings.selected_output

        self.input_settings = {
             'connection_name': self.selected_input,
             'connection_status': self.settings.input_connection_status,
             'disconnected_label': self.settings.input_disconnected_label,
        }

        self.output_settings = {
             'connection_name': self.selected_output,
             'connection_status': self.settings.output_connection_status,
             'disconnected_label': self.settings.output_disconnected_label             
        }

        # Local constants
        self.name = 'Quick Configuration'
        self.options = {'sticky':'w', 'padx':10, 'pady':(10, 5)} # widgit placement options
        self.new_patch_label = '< new instrument >'

        # Local variables
        self.ready_state = tk.StringVar(value='Unconnected')
        self.patch_var = tk.StringVar(value=self.saved_patches_list[0]) # patch menu selection
        
        # Configure grid
        for i in range(6):
            self.columnconfigure(i, weight=1)

        for i in range(2):
            self.rowconfigure(i, weight=1)

        self._create_widgets()
        if self.ready_state.get() == 'Ready':
            self.start_button.focus()
        else:
            self.connections_button.focus()

        # Auto-load default patch if any, otherwise load new patch
        self._initiate_menu()

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

        # Manage patch menu state and patch loading
        self.running_status.trace_add('write', self._update_patch_menu_state)
        self._update_patch_menu_state()
        self.patch_var.trace_add('write', self._load_selected_patch)
        self._load_selected_patch()

        # Manage patch menu list
        self.default_patch.trace_add('write', self._update_patch_menu_items)
        self._update_patch_menu_items()

        # Keep input status colors and text in sync
        self._create_status_tracer(self.input_settings['connection_name'], self.input_status_label, **self.input_settings)
        self._create_status_tracer(self.input_settings['connection_status'], self.input_status_label, **self.input_settings)
        self._update_status(self.input_status_label, **self.input_settings)

        # Keep output status colors and text in sync
        self._create_status_tracer(self.output_settings['connection_name'], self.output_status_label, **self.output_settings)
        self._create_status_tracer(self.output_settings['connection_status'], self.output_status_label, **self.output_settings)
        self._update_status(self.output_status_label, **self.output_settings)


    def _create_widgets(self):
        # Start/Stop button, status icon and label
        self.ready_frame = ttk.Frame(self, relief='solid')
        self.ready_frame.grid(column=0, row=0, rowspan=3, sticky='w', padx=10, pady=10)

        self.status_icon = tk.Canvas(self.ready_frame, width=14, height=14, highlightthickness=0)
        self.status_icon_id = self.status_icon.create_oval(2, 2, 12, 12, fill='red', outline='')
        self.status_icon.grid(column=0, row=0, stick='w', padx=10, pady=(10, 5))

        self.ready_label = ttk.Label(self.ready_frame, textvariable=self.ready_state)
        self.ready_label.grid(column=1, row=0, sticky='w', padx=(0, 10), pady=(10, 5))

        self.start_button = ttk.Button(self.ready_frame, text='PLAY', command=self._on_start_button)
        self.start_button.grid(column=0, row=1, columnspan=2, sticky='w', padx=10, pady=10)

        # Input information
        self.input_frame = ttk.Frame(self)
        self.input_frame.grid(column=1, row=0, columnspan=2, sticky='w', padx=0)
        self.input_label = ttk.Label(self.input_frame, text='Input Device:')
        self.input_label.grid(column=0, row=0, sticky='w', padx=5, pady=(10, 5))
        self.input_status_label = ttk.Label(self.input_frame, width=15)
        self.input_status_label.grid(column=1, row=0, sticky='w', padx=0, pady=(10, 5))

        # Output information
        self.output_frame = ttk.Frame(self)
        self.output_frame.grid(column=3, row=0, columnspan=2, sticky='w', padx=5)
        self.output_label = ttk.Label(self.output_frame, text='MIDI Port:')
        self.output_label.grid(column=0, row=0, sticky='w', padx=5, pady=(10, 5))
        self.output_status_label = ttk.Label(self.output_frame, width=15)
        self.output_status_label.grid(column=1, row=0, sticky='w', padx=0, pady=(10, 5))

        # Connections button
        self.connections_button = ttk.Button(
            self, 
            text='Connections', 
            width=9, 
            style='Default.TButton',
            command=self._on_connections_button
            )
        self.connections_button.grid(column=5, row=0, sticky='e', padx=10, pady=(10, 10))

        # Separate connections from instrument
        self.separator = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.separator.grid(column=1, row=1, columnspan=5, sticky='ew', padx=(5, 10))

        # Load patches (instruments)
        self.patches_frame = ttk.Frame(self)
        self.patches_frame.grid(column=1, row=2, sticky='ew', columnspan=4, padx=0)
        self.patches_frame.columnconfigure(1, weight=1)
        self.instrument_label = ttk.Label(self.patches_frame, text='Instrument:')
        self.instrument_label.grid(column=0, row=0, sticky='w', padx=5, pady=10)

        self.patch_menu = ttk.OptionMenu(
            self.patches_frame,
            self.patch_var,
            self.saved_patches_list[0],
            *self.saved_patches_list
            )
        self.patch_menu.grid(column=1, row=0, sticky='ew', padx=(10, 5), pady=10)

        self.controls_button = ttk.Button(
            self, 
            text='Controls', 
            width=9, 
            style='Default.TButton',
            command=self._on_controls_button
            )
        self.controls_button.grid(column=5, row=2, sticky='e', padx=10, pady=(10, 10))

    def _create_status_tracer(self, variable: tk.Variable, label: ttk.Label, **global_settings) -> None:
            """Creates a global variable tracer assigns it to a label, and passes it a Dict of arguments"""
            variable.trace_add(
                'write',
                lambda *args: self._update_status(status_label=label, **global_settings)
            )
         
    def _update_status(
            self, 
            status_label: ttk.Label, 
            connection_name: tk.StringVar, 
            connection_status: tk.BooleanVar, 
            disconnected_label: str
        ) -> None:
        """Updates connection status label with correct color."""
        name = connection_name.get().removesuffix('._websocket._tcp.local.')

        if not name or name == disconnected_label: # no default or connected device available
            display_text = disconnected_label
            color = 'red'
        elif connection_status.get(): # device connected
            display_text = name
            color = 'green'
        else:
            color = 'blue' # default device available but unconnected
            display_text = name
        status_label.config(foreground=color, text=display_text)

    def _update_start_button_state(self, *args) -> None:
        """Enables start button only if input and output are available, and sets status."""
        input_connection = self.selected_input.get()
        output_connection = self.selected_output.get()
        ready = bool(input_connection) and bool(output_connection)
        running = self.settings.running_status.get()

        # Set status icon color
        if running:
            icon_color = 'green'
            self.ready_state.set('Running')
        elif ready:
            icon_color = 'blue'
            self.ready_state.set('Ready')
        else:
            icon_color = 'red'
            self.ready_state.set('Unconnected')

        self.status_icon.itemconfig(self.status_icon_id, fill=icon_color)

        # Set start button state
        if ready: 
            self.start_button.config(state='normal')
        else:
            self.start_button.config(state='disabled')

            # Reset state on disconnect
            if running:
                self.settings.running_status.set(False)
                self.start_button.config(text='START')
                return

    def _update_patch_menu_items(self, *args) -> None:
        """Rebuilds the list of patches and updates the OptionMenu entries."""
        # Update the local patches list with new default tags
        self.saved_patches_list = [
            f"{patch} (default)" if patch == self.default_patch.get() else patch # tag default patch
            for patch in self.settings.saved_patches_list
            ]

        # Get menu reference
        menu = self.patch_menu['menu']
        menu.delete(0, 'end')

        # Refresh menu options
        for patch in self.saved_patches_list:
            menu.add_command(
                label=patch,
                command=tk._setit(self.patch_var, patch)
            )

        # Update current selection if it matches the new default
        default_patch_tagged = f"{self.default_patch.get()} (default)"
        if default_patch_tagged in self.saved_patches_list:
            self.patch_var.set(default_patch_tagged)

    def _update_patch_menu_state(self, *args) -> None:
        """Disables patch selection menu if running."""
        running = self.running_status.get()
        if running:
            self.patch_menu.config(state='disabled')
        else:
            self.patch_menu.config(state='normal')

    def _load_patch(self, patch_name: str) -> None:
        """Loads the specified patch."""

        # Patch already active
        if patch_name == self.loaded_patch_name.get():
            return

        # Strip ' (default)' tag to match dictionary keys in saved_patches_data
        clean_patch_name = patch_name.replace(' (default)', '')

        # Fetch patch data safely
        patches_data = getattr(self.settings, 'saved_patches_data', {}).get('patches', {})
        if clean_patch_name in patches_data:
            selected_patch_data = patches_data[clean_patch_name]

            # Update description StringVars
            self.loaded_patch_description.set(selected_patch_data.get('description', ''))

            # Update parameters dictionary in settings and local pointer
            parameters = selected_patch_data.get('parameters', {})
            self.settings.loaded_patch_parameters_data = parameters
            self.loaded_patch_parameters_data = parameters

            # Set last as it triggers mapping GUI re-draw
            self.loaded_patch_name.set(patch_name)

    def _load_selected_patch(self, *args) -> None:
        """Loads the patch selected in the patch menu."""
        patch_name = self.patch_var.get()
        self._load_patch(patch_name=patch_name)


    def _update_tabs_buttons(self, active_tab: str | None) -> None:
        """Highlights the button of the active tab and hides the other."""
        if active_tab == 'connections':
            self.connections_button.config(style='Active.TButton')
            self.controls_button.config(style='Default.TButton')
        elif active_tab == 'controls':
            self.controls_button.config(style='Active.TButton')
            self.connections_button.config(style='Default.TButton')
        else:
            # Both closed
            self.connections_button.config(style='Default.TButton')
            self.controls_button.config(style='Default.TButton')

    def _initiate_menu(self, *args) -> None:
        """Set initial menu selection to the default patch if any."""
        default_patch = self.default_patch.get()
        if default_patch and (default_patch + ' (default)') in self.saved_patches_list:
            self.patch_var.set(default_patch + ' (default)')
        else:
            self.patch_var.set(self.saved_patches_list[0])

    def _on_start_button(self) -> None:
        running = self.settings.running_status.get()
        if not running:
            self.settings.running_status.set(True)
            self.start_button.config(text='STOP', style='Active.TButton')
        else:
            self.settings.running_status.set(False)
            self.start_button.config(text='PLAY', style='Default.TButton')

    def _on_connections_button(self) -> None:
        """Toggles visibility of connections frame."""
        self.master._toggle_tabs('connections') # type: ignore

    def _on_controls_button(self) -> None:
        """Toggles visibility of controls frame."""
        self.master._toggle_tabs('controls') # type: ignore


            

