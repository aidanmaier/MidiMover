import tkinter as tk
from tkinter import ttk
from gui.widgets import RangeSlider

class ControlsFrame(ttk.Frame):
    def __init__(self, container, settings):
        super().__init__(container)

        # Pointers to global settings
        self.settings = settings
        self.input_parameter_types = self.settings.input_parameter_types
        self.output_parameter_types = self.settings.output_parameter_types
        self.default_patch: tk.StringVar = self.settings.default_patch
        self.loaded_patch_name: tk.StringVar = self.settings.loaded_patch_name
        self.loaded_patch_description: tk.StringVar = self.settings.loaded_patch_description
        self.loaded_patch_parameters_data: dict = self.settings.loaded_patch_parameters_data

        # Local constants
        self.name = 'Controls'
        self.options = {'sticky':'w', 'padx':10, 'pady':(10, 5)} # widgit placement options

        # Local variables
        self.patch_altered = tk.BooleanVar(value=False)

        # Track parameter types so only one of each is ever used
        self.available_input_types = [x for x in self.input_parameter_types]
        self.available_output_types = [x for x in self.output_parameter_types]

        # Track dynamically created parameter widgets for cleanup
        self.parameter_selector_widgets = [] # ((in_selector_var, in_selector), (out_selector_var, out_selector))
        self.parameter_slider_widgets = [] # (in_slider, out_slider)
    
        # Configure grid
        for i in range(0, 3):
            self.columnconfigure(i, weight=1)
        self.rowconfigure(3, weight=1) # control mapping header

        self._create_widgets()
        
        # Manage save patch button state
        self.patch_altered.trace_add('write', self._update_save_patch_button_state)
        self._update_save_patch_button_state()

        # Manage new patch loaded
        self.loaded_patch_name.trace_add('write', self._update_parameter_list)
        self._update_parameter_list()
    
    def _create_widgets(self):
        # Patch info
        self.patch_name_frame = ttk.Frame(self)
        self.patch_name_frame.grid(column=0, row=0, columnspan=2, **self.options)
        self.patch_name_label = ttk.Label(self.patch_name_frame, text='Instrument:', width=10)
        self.patch_name_label.pack(side='left')
        self.patch_name = ttk.Label(self.patch_name_frame, textvariable=self.loaded_patch_name)
        self.patch_name.pack(side='left')

        self.patch_description_frame = ttk.Frame(self)
        self.patch_description_frame.grid(column=0, row=1, columnspan=3, sticky='ew', padx=10, pady=5)
        self.patch_description_label = ttk.Label(self.patch_description_frame, text='Description:', width=10)
        self.patch_description_label.pack(side='left')
        self.patch_description = ttk.Label(self.patch_description_frame, textvariable=self.loaded_patch_description)
        self.patch_description.pack(side='left')

        self.save_patch_button = ttk.Button(self, text='Save Patch', state='disabled', command=self._on_save_patch_button)
        self.save_patch_button.grid(column=2, row=0, sticky='e', padx='10', pady=(10, 5))

        # Separate patch info from control mapping
        self.seperator_upper = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.seperator_upper.grid(column=0, row=2, columnspan=3, sticky='ew', padx=10, pady=(10, 5))

        # Control mapping
        self.parameters_frame = ttk.Frame(self)
        self.parameters_frame.grid(column=0, row=3, columnspan=3, sticky='nsew')
        self.parameters_frame.columnconfigure(0, weight=1) # Input frame
        self.parameters_frame.columnconfigure(1, weight=0) # Separator column
        self.parameters_frame.columnconfigure(2, weight=1) # Output frame
        self.parameters_frame.rowconfigure(0, weight=1)

        self.input_mapping_frame = self._build_mapping_frame(0, 'Input')

        # Separate input and output mapping
        self.seperator_vert = ttk.Separator(self.parameters_frame, orient=tk.VERTICAL)
        self.seperator_vert.grid(column=1, row=0, sticky='ns', padx=5, pady=(0, 5))

        self.output_mapping_frame = self._build_mapping_frame(2, 'Output')

    def _update_save_patch_button_state(self, *args) -> None:
        """Disables save patch button if no changes have been made."""
        if self.patch_altered.get():
            self.save_patch_button.config(state='normal')
        else:
            self.save_patch_button.config(state='disabled')

    def _build_mapping_frame(self, col, connection):
        """Builds frame to hold input or output parameter controls."""
        frame = ttk.Frame(self.parameters_frame)
        frame.grid(column=col, row=0, sticky='nsew')
        frame.columnconfigure(0, weight=1)
        frame.columnconfigure(1, weight=2)

        parameter_label = ttk.Label(frame, text=f'{connection}')
        parameter_label.grid(column=0, row=0, sticky='w', padx=10, pady=0)

        range_label = ttk.Label(frame, text='Range')
        range_label.grid(column=1, row=0, sticky='w', padx=10, pady=0)

        self.separator = ttk.Separator(frame, orient=tk.HORIZONTAL)
        self.separator.grid(column=0, row=1, columnspan=2, sticky='ew', padx=10, pady=(10, 5))

        return frame

    def _build_parameter_controls(self, index, input_frame, output_frame):
        """Builds input/output parameter mapping controls."""
        param_data = self.loaded_patch_parameters_data[str(index)]
        row = index + 2  # add widgets on rows 2 to 5

        # Guards for empty values
        input_param = param_data['input'] if param_data['input'] else None
        input_range = param_data['input_range'] if len(param_data['input_range']) > 1 else [0, 100]
        output_param = param_data['output'] if param_data['output'] else None
        output_range = param_data['output_range'] if len(param_data['output_range']) > 1 else [0, 100]

        input_param_var = tk.StringVar(value=input_param)
        input_param_selector = ttk.Combobox(
            input_frame,
            textvariable=input_param_var,
            values=[],  # populated by _refresh_available_types() after all rows are built
            width=6,
            state='readonly',
        )
        input_param_selector.grid(column=0, row=row, sticky='w', padx=(10, 0), pady=15)
        input_param_selector.bind('<<ComboboxSelected>>', lambda e: self._on_type_selected())

        input_param_slider = RangeSlider(
            input_frame,
            from_=0,
            to=100,
            low=input_range[0],
            high=input_range[1],
            width=160,
            command=lambda lo, hi: self._on_parameter_change()
        )
        input_param_slider.grid(column=1, row=row, sticky='ew', padx=(5, 10), pady=15)

        output_param_var = tk.StringVar(value=output_param)
        output_param_selector = ttk.Combobox(
            output_frame,
            textvariable=output_param_var,
            values=[],
            width=6,
            state='readonly',
        )
        output_param_selector.grid(column=0, row=row, sticky='w', padx=(10, 0), pady=15)
        output_param_selector.bind('<<ComboboxSelected>>', lambda e: self._on_type_selected())

        output_param_slider = RangeSlider(
            output_frame,
            from_=0,
            to=100,
            low=output_range[0],
            high=output_range[1],
            width=160,
            command=lambda lo, hi: self._on_parameter_change()
        )
        output_param_slider.grid(column=1, row=row, sticky='ew', padx=(5, 10), pady=15)

        # Keep references alive + enable later lookup/cleanup
        self.parameter_selector_widgets.append(((input_param_var, input_param_selector), (output_param_var, output_param_selector)))
        self.parameter_slider_widgets.append((input_param_slider, output_param_slider))

    def _refresh_available_types(self) -> None:
        """Handles available parameter types across all rows so no type can be used more than once."""
        input_selections = [
            in_var.get() for (in_var, in_sel), (out_var, out_sel) in self.parameter_selector_widgets
            if in_var.get()
        ]
        output_selections = [
            out_var.get() for (in_var, in_sel), (out_var, out_sel) in self.parameter_selector_widgets
            if out_var.get()
        ]

        for (in_var, in_sel), (out_var, out_sel) in self.parameter_selector_widgets:
            own_input = in_var.get()
            available_input = [
                t for t in self.input_parameter_types
                if t not in input_selections or t == own_input
            ]
            in_sel['values'] = available_input

            own_output = out_var.get()
            available_output = [
                t for t in self.output_parameter_types
                if t not in output_selections or t == own_output
            ]
            out_sel['values'] = available_output

    def _update_parameter_list(self, *args) -> None:
        """Refreshes patch data, clears and rebuilds parameter controls."""
        # Destroy existing parameter control widgets
        for (in_var, in_sel), (out_var, out_sel) in self.parameter_selector_widgets:
            in_sel.destroy()
            out_sel.destroy()
        for in_slider, out_slider in self.parameter_slider_widgets:
            in_slider.destroy()
            out_slider.destroy()
        self.parameter_selector_widgets.clear()
        self.parameter_slider_widgets.clear()

        self.loaded_patch_parameters_data = self.settings.loaded_patch_parameters_data

        # Parameter controls
        for i in range(5):
            self._build_parameter_controls(i, self.input_mapping_frame, self.output_mapping_frame)

        # Populate dropdown values now that all rows/selections exist
        self._refresh_available_types()
        self.patch_altered.set(False)

    def _on_type_selected(self) -> None:
        """Called when a parameter-type combobox selection changes."""
        self._on_parameter_change()
        self._refresh_available_types()

    def _on_parameter_change(self) -> None:
        """Flag parameter settings changes to activate Save Patch button."""
        self.patch_altered.set(True)

    def _on_save_patch_button(self):
        pass
