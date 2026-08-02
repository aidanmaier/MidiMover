import json
import tkinter as tk
from tkinter import ttk
from typing import Any
from settings import Settings
from gui.widgets import RangeSlider

class ControlsFrame(ttk.Frame):
    def __init__(self, container, settings: Settings):
        super().__init__(container)

        # Pointers to global settings
        self.settings = settings
        self.note_names: list[str] = self.settings.note_names
        self.scale_patterns: dict[str, Any] = self.settings.scale_patterns
        self.input_parameter_types: list[str] = self.settings.input_parameter_types
        self.output_parameter_types: list[str] = self.settings.output_parameter_types

        self.default_scale: tk.StringVar = self.settings.default_scale
        self.default_root_note: tk.IntVar = self.settings.default_root_note # root note number
        self.default_root_name: tk.StringVar = self.settings.default_root_name
        self.default_patch: tk.StringVar = self.settings.default_patch

        self.loaded_patch_name: tk.StringVar = self.settings.loaded_patch_name
        self.loaded_patch_description: tk.StringVar = self.settings.loaded_patch_description
        self.loaded_patch_parameters_data: dict = self.settings.loaded_patch_parameters_data

        self.active_scale: tk.StringVar = self.settings.active_scale
        self.active_root_note: tk.IntVar = self.settings.active_root_note
        self.active_root_name: tk.StringVar = self.settings.active_root_name

        # Local constants
        self.name = 'Controls'
        self.options = {'sticky':'w', 'padx':10, 'pady':(10, 5)} # widgit placement options

        # Local variables
        self.patch_altered = tk.BooleanVar(value=False)
        self.cleaned_loaded_patch_name = tk.StringVar(value='') # default tag stripped

        # Track parameter types so only one of each is ever used
        self.available_input_types = [x for x in self.input_parameter_types]
        self.available_output_types = [x for x in self.output_parameter_types]

        # Track dynamically created parameter widgets for cleanup
        self.parameter_selector_widgets = [] # ((in_selector_var, in_selector), (out_selector_var, out_selector))
        self.parameter_slider_widgets = [] # (in_slider, out_slider)
    
        # Configure grid
        for i in range(3):
            self.columnconfigure(i, weight=1)
        self.rowconfigure(3, weight=1) # control mapping header

        self._create_widgets()
        
        # Handle patch button states
        self.patch_altered.trace_add('write', self._update_patch_button_states)
        self._update_patch_button_states()
  
        # Handle new patch loaded
        self.loaded_patch_name.trace_add('write', self._update_parameter_list)
        self._update_parameter_list()

        self.default_patch.trace_add('write', self._update_default_patch_button)
        self.loaded_patch_name.trace_add('write', self._update_default_patch_button)
        self._update_default_patch_button()

        # Handle default scale or root note changes
        self.active_scale.trace_add('write', self._update_default_scale_button_state)
        self.active_root_name.trace_add('write', self._update_default_scale_button_state)
        self.active_root_name.trace_add('write', self._update_active_root_note)
        self._update_default_scale_button_state()
    
    def _create_widgets(self):
        # Patch info
        self.patch_name_frame = ttk.Frame(self)
        self.patch_name_frame.grid(column=0, row=0, columnspan=2, **self.options)
        self.patch_name_label = ttk.Label(self.patch_name_frame, text='Instrument:', width=10)
        self.patch_name_label.pack(side='left')
        self.patch_name = ttk.Label(self.patch_name_frame, textvariable=self.cleaned_loaded_patch_name)
        self.patch_name.pack(side='left')

        self.patch_description_frame = ttk.Frame(self)
        self.patch_description_frame.grid(column=0, row=1, columnspan=3, sticky='ew', padx=10, pady=5)
        self.patch_description_label = ttk.Label(self.patch_description_frame, text='Description:', width=10)
        self.patch_description_label.pack(side='left')
        self.patch_description = ttk.Label(self.patch_description_frame, textvariable=self.loaded_patch_description)
        self.patch_description.pack(side='left')

        # Save/Reset/Set Default buttons
        self.patch_button_frame = ttk.Frame(self)
        self.patch_button_frame.grid(column=2, row=0, sticky='ew')

        self.save_patch_button = ttk.Button(
            self.patch_button_frame, 
            text='Save', 
            state='disabled', 
            command=self._on_save_patch_button
            )
        self.save_patch_button.grid(column=0, row=0, sticky='w', padx=5, pady=(10, 5))

        self.reset_patch_button = ttk.Button(
            self.patch_button_frame, 
            text='Reset', 
            state='disabled', 
            command=self._on_reset_patch_button
            )
        self.reset_patch_button.grid(column=1, row=0, sticky='ew', padx=(0, 5), pady=(10, 5))

        self.default_patch_button = ttk.Button(
            self.patch_button_frame, 
            text='Set as Default', 
            state='normal',
            command=self._on_default_patch_button
            )
        self.default_patch_button.grid(column=2, row=0, sticky='e', padx=0, pady=(10, 5))

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

        # Separate mapping from scale settings
        self.seperator_lower = ttk.Separator(self.parameters_frame, orient=tk.HORIZONTAL)
        self.seperator_lower.grid(column=0, row=4, columnspan=3, sticky='ew', padx=10, pady=5)

        # Musical scale settings
        self.scale_frame = ttk.Frame(self)
        self.scale_frame.grid(column=0, row=5, columnspan=2, sticky='ew')
        self.scale_frame.columnconfigure(0, weight=1)
        self.scale_frame.columnconfigure(1, weight=2)
        self.scale_frame.columnconfigure(2, weight=1)
        self.scale_frame.columnconfigure(3, weight=2)

        self.root_label = ttk.Label(self.scale_frame, text='Root Note:')
        self.root_label.grid(column=0, row=0, sticky='w', padx=10, pady=10)
        self.root_var_selector = ttk.Combobox(
            self.scale_frame,
            textvariable=self.active_root_name,
            values=self.note_names,
            width=4,
            state='readonly',
        )
        self.root_var_selector.grid(column=1, row=0, sticky='w', padx=10, pady=10)

        self.scale_label = ttk.Label(self.scale_frame, text='Scale:')
        self.scale_label.grid(column=2, row=0, sticky='w', padx=10, pady=10)

        self.scale_var_selector = ttk.Combobox(
            self.scale_frame,
            textvariable=self.active_scale,
            values=list(self.scale_patterns.keys()),
            width=14,
            state='readonly',
        )
        self.scale_var_selector.grid(column=3, row=0, sticky='w', padx=10, pady=10)

        self.default_scale_frame = ttk.Frame(self)
        self.default_scale_frame.grid(column=2, row=5, columnspan=2, sticky='ew')
        self.default_scale_frame.columnconfigure(0)
        self.default_scale_frame.columnconfigure(1)
        self.default_scale_frame.columnconfigure(2)

        self.default_scale_button = ttk.Button(
            self.default_scale_frame, 
            text='Set as Default Scale',
            state='disabled', 
            width=14,
            command=self._on_default_scale_button
            )
        self.default_scale_button.grid(column=0, row=0, sticky='w', padx=5, pady=10)

        self.default_scale_label = ttk.Label(self.default_scale_frame, text='Default:')
        self.default_scale_label.grid(column=1, row=0, sticky='w', padx=5, pady=10)
        self.default_root_var_label = ttk.Label(self.default_scale_frame, textvariable=self.default_root_name, width=3)
        self.default_root_var_label.grid(column=2, row=0, sticky='w', padx=0, pady=10)
        self.default_scale_var_label = ttk.Label(self.default_scale_frame, textvariable=self.default_scale, width=12)
        self.default_scale_var_label.grid(column=3, row=0, sticky='w', padx=(0, 10), pady=10)

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
        # Ensure the index key exists in dictionary before reading
        str_index = str(index)
        param_data = self.loaded_patch_parameters_data.get(
            str_index, 
            {'input': None, 'input_range': [0, 100], 'output': None, 'output_range': [0, 100]} # default parameter values
        )
        row = index + 2  # add widgets on rows 2 to 5

        # Guards for empty values
        input_param = param_data.get('input', None)
        input_range = param_data.get('input_range') if len(param_data.get('input_range', [])) > 1 else [0, 100]
        output_param = param_data.get('output', None)
        output_range = param_data.get('output_range') if len(param_data.get('output_range', [])) > 1 else [0, 100]

        input_param_var = tk.StringVar(value=input_param)
        input_param_selector = ttk.Combobox(
            input_frame,
            textvariable=input_param_var,
            values=[],
            width=6,
            state='readonly',
        )
        input_param_selector.grid(column=0, row=row, sticky='w', padx=(10, 0), pady=15)
        # Pass row index to callback
        input_param_selector.bind('<<ComboboxSelected>>', lambda e, idx=index: self._on_type_selected(idx))

        input_param_slider = RangeSlider(
            input_frame,
            from_=0,
            to=127,
            low=input_range[0],
            high=input_range[1],
            width=200,
            # Pass row index, low, and high values to callback
            command=lambda lo, hi, idx=index: self._on_slider_change(idx, 'input_range', lo, hi)
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
        # Pass row index to callback
        output_param_selector.bind('<<ComboboxSelected>>', lambda e, idx=index: self._on_type_selected(idx))

        output_param_slider = RangeSlider(
            output_frame,
            from_=0,
            to=127, # midi range
            low=output_range[0],
            high=output_range[1],
            width=200,
            # Pass row index, low, and high values to callback
            command=lambda lo, hi, idx=index: self._on_slider_change(idx, 'output_range', lo, hi)
        )
        output_param_slider.grid(column=1, row=row, sticky='ew', padx=(5, 10), pady=15)

        # Keep references alive
        self.parameter_selector_widgets.append(((input_param_var, input_param_selector), (output_param_var, output_param_selector)))
        self.parameter_slider_widgets.append((input_param_slider, output_param_slider))

    def _sync_row_data(self, index: int):
        """Updates dictionary entry for a specific row index from its current widget values."""
        str_index = str(index)
        (in_var, _), (out_var, _) = self.parameter_selector_widgets[index]
        in_slider, out_slider = self.parameter_slider_widgets[index]

        # Ensure dictionary entry exists
        if str_index not in self.loaded_patch_parameters_data:
            self.loaded_patch_parameters_data[str_index] = {}

        # Update dictionary values directly
        in_low = in_slider.low_var.get()
        in_high =in_slider.high_var.get()
        out_low = out_slider.low_var.get()
        out_high =out_slider.high_var.get()

        self.loaded_patch_parameters_data[str_index]['input'] = in_var.get() or None
        self.loaded_patch_parameters_data[str_index]['input_range'] = [int(in_low), int(in_high)]
        self.loaded_patch_parameters_data[str_index]['output'] = out_var.get() or None
        self.loaded_patch_parameters_data[str_index]['output_range'] = [int(out_low), int(out_high)]

    def _on_type_selected(self, index: int) -> None:
        """Called when a parameter-type combobox selection changes."""
        self._sync_row_data(index)
        self._refresh_available_types()
        self._on_parameter_change()

    def _on_slider_change(self, index: int, range_key: str, low: float, high: float) -> None:
        """Called when a range slider changes."""
        str_index = str(index)
        if str_index not in self.loaded_patch_parameters_data:
            self.loaded_patch_parameters_data[str_index] = {}

        # if range_key == 'input_range

        self.loaded_patch_parameters_data[str_index][range_key] = [low, high]
        self._on_parameter_change()

    def _update_parameter_list(self, *args) -> None:
        """Refreshes patch data, clears and rebuilds parameter controls."""
        loaded_patch = self.loaded_patch_name.get()
        self.cleaned_loaded_patch_name.set(loaded_patch.removesuffix(' (default)'))

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
        for i in range(4):
            self._build_parameter_controls(i, self.input_mapping_frame, self.output_mapping_frame)

        # Populate dropdown values now that all rows/selections exist
        self._refresh_available_types()
        self.patch_altered.set(False)

    def _update_default_scale_button_state(self, *args) -> None:
        """Disables set default scale button if default already loaded."""
        matching_scales = self.active_scale.get() == self.default_scale.get()
        matching_roots = self.active_root_note.get() == self.default_root_note.get()

        if matching_scales and matching_roots:
            self.default_scale_button.config(state='disabled')
        else:
            self.default_scale_button.config(state='normal')
        
    def _update_patch_button_states(self, *args) -> None:
        """Disables save patch button if no changes have been made."""
        if self.patch_altered.get():
            self.save_patch_button.config(state='normal')
            self.reset_patch_button.config(state='normal')
        else:
            self.save_patch_button.config(state='disabled')
            self.reset_patch_button.config(state='disabled')

    def _update_default_patch_button(self, *args) -> None:
        """Disables Set Default if default patch already loaded."""
        loaded_patch = self.loaded_patch_name.get().removesuffix(' (default)')
        default_patch = self.default_patch.get()

        if loaded_patch == '< new instrument >' or loaded_patch == default_patch:
            self.default_patch_button.config(state='disabled')
        else:
            self.default_patch_button.config(state='normal')

    def _update_active_root_note(self, *args):
        """Updates actvie root note based on active root name."""
        new_root_note = self.note_names.index(self.active_root_name.get())
        self.active_root_note.set(new_root_note)

    def _on_parameter_change(self) -> None:
        """Flag parameter settings changes to activate Save Patch button."""
        self.patch_altered.set(True)


    def _on_save_patch_button(self) -> None:
        """Saves current patch parameter configuration to Settings and settings.json."""
        patch_name = self.loaded_patch_name.get().removesuffix(' (default)')
        
        # Update active patch data inside Settings.saved_patches_data
        if patch_name in self.settings.saved_patches_data.get('patches', {}):
            self.settings.saved_patches_data['patches'][patch_name]['parameters'] = self.loaded_patch_parameters_data
            
            # Save patches file to json
            with open(self.settings.patches_filepath, 'w') as f:
                json.dump(self.settings.saved_patches_data, f, indent=4)

        # Save global settings
        self.settings._save_current_settings()
        self.patch_altered.set(False)

    def _on_reset_patch_button(self) -> None:
        """Reloads current patch from patch.json."""
        self.master.master.header._load_patch(self.loaded_patch_name.get()) # type: ignore
        self._update_parameter_list()

    def _on_default_patch_button(self) -> None:
        """Saves loaded patch as default in settings.json."""
        loaded_patch = self.loaded_patch_name.get().removesuffix(' (default)')
        self.default_patch.set(loaded_patch)

    def _on_default_scale_button(self) -> None:
        """Saves active scale and root note as defaults Settings"""
        # Update default scale and root in settings
        active_scale = self.active_scale.get()
        active_root_note = self.active_root_note.get()
        active_root_name = self.active_root_name.get()
        self.default_scale.set(active_scale)
        self.default_root_note.set(active_root_note)
        self.default_root_name.set(active_root_name)


        