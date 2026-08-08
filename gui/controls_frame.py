import json
import tkinter as tk
from tkinter import ttk
from typing import Any
from settings import Settings
from output import midi_to_signed_pitch, snap_to_scale
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
        self.default_patch: tk.StringVar = self.settings.default_patch

        self.loaded_patch_name: tk.StringVar = self.settings.loaded_patch_name
        self.loaded_patch_description: tk.StringVar = self.settings.loaded_patch_description
        # self.settings.loaded_patch_parameters_data: dict = self.settings.settings.loaded_patch_parameters_data

        self.active_scale: tk.StringVar = self.settings.active_scale
        self.active_root_note: tk.IntVar = self.settings.active_root_note
        self.active_root_name: tk.StringVar = self.settings.active_root_name

        self.running_status: tk.BooleanVar = self.settings.running_status
        self.active_midi_channel: tk.IntVar = self.settings.active_midi_channel

        # Local constants
        self.name = 'Controls'
        self.options = {'sticky':'w', 'padx':10, 'pady':(10, 5)} # widgit placement options

        # Local variables
        self.patch_altered = tk.BooleanVar(value=False)
        self.cleaned_loaded_patch_name = tk.StringVar(value='') # default tag stripped
        self.display_midi_channel = tk.IntVar(value=self.active_midi_channel.get() + 1) # 1-indexed for UI

        # Track parameter types so only one of each is ever used
        self.available_input_types = [x for x in self.input_parameter_types]
        self.available_output_types = [x for x in self.output_parameter_types]

        # Track dynamically created parameter widgets for cleanup
        self.parameter_selector_widgets = [] # ((in_selector_var, in_selector), (out_selector_var, out_selector))
        self.parameter_slider_widgets = [] # (in_slider, out_slider)

        # Track active output parameters
        self.active_output_tracker = {}  # {row_index: "Previous_Output_Name"}
    
        # Configure grid
        for i in range(3):
            self.columnconfigure(i, weight=1)

        self._create_widgets()

        # Handle running status change
        self.running_status.trace_add('write', self._update_channel_selector_state)

        # Handle MIDI channel changes
        self.active_midi_channel.trace_add('write', self._on_parameter_change)
        self.active_midi_channel.trace_add('write', self._on_active_channel_changed)
        self.display_midi_channel.trace_add('write', self._on_display_channel_changed)
        
        # Handle patch button states
        self.patch_altered.trace_add('write', self._update_patch_button_states)
        self._update_patch_button_states()
  
        # Handle new patch loaded
        self.loaded_patch_name.trace_add('write', self._update_parameter_list)
        self._update_parameter_list()

        self.default_patch.trace_add('write', self._update_default_patch_button)
        self.loaded_patch_name.trace_add('write', self._update_default_patch_button)
        self._update_default_patch_button()

        # Handle scale and root changes
        self.active_root_name.trace_add('write', self._update_active_root_note)
        self.active_scale.trace_add('write', self._on_parameter_change)
        self.active_root_name.trace_add('write', self._on_parameter_change)
    
    def _create_widgets(self):
        # Patch info
        self.patch_name_frame = ttk.Frame(self)
        self.patch_name_frame.grid(column=0, row=0, columnspan=2, **self.options)
        self.patch_name_label = ttk.Label(self.patch_name_frame, text='Instrument:', width=10)
        self.patch_name_label.pack(side='left')
        self.patch_name = ttk.Label(self.patch_name_frame, textvariable=self.cleaned_loaded_patch_name)
        self.patch_name.pack(side='left')

        # Save/Reset/Set Default buttons
        self.patch_button_frame = ttk.Frame(self)
        self.patch_button_frame.grid(column=2, columnspan=2, row=0, sticky='ew', padx=10)

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

        # Patch description
        self.patch_description_frame = ttk.Frame(self)
        self.patch_description_frame.grid(column=0, row=1, columnspan=3, sticky='ew', padx=10, pady=5)
        self.patch_description_frame.columnconfigure(2, weight=1)

        self.patch_description_label = ttk.Label(self.patch_description_frame, text='Description:', width=10)
        self.patch_description_label.grid(column=0, row=0)
        self.patch_description = ttk.Label(self.patch_description_frame, textvariable=self.loaded_patch_description)
        self.patch_description.grid(column=1, row=0)

        # MIDI channel selector
        self.channel_frame = ttk.Frame(self.patch_description_frame)
        self.channel_frame.grid(column=3, row=0, sticky='e')

        self.channel_label = ttk.Label(self.channel_frame, text='MIDI Channel:')
        self.channel_label.grid(column=0, row=0, padx=5)

        self.channel_selector = ttk.Spinbox(
            self.channel_frame,
            from_=1,
            to=16,
            textvariable=self.display_midi_channel,
            width=3,
        )
        self.channel_selector.grid(column=1, row=0)

        # Separate description from controls
        self.separator_upper = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.separator_upper.grid(column=0, row=2, columnspan=3, sticky='ew', padx=10, pady=(10, 5))

        # Parameter mapping header
        self.parameters_header = ttk.Frame(self)
        self.parameters_header.grid(column=0, row=3, columnspan=3, sticky='ew')

        self.input_param_label = ttk.Label(self.parameters_header, text='Motion Parameters', width=33)
        self.input_param_label.grid(column=0, row=0, sticky='w', padx=10, pady=0)
        self.map_param_label = ttk.Label(self.parameters_header, text='map to -->', width=10)
        self.map_param_label.grid(column=1, row=0, sticky='w', padx=(10, 0), pady=0)
        self.output_param_label = ttk.Label(self.parameters_header, text='MIDI Parameters', width=30)
        self.output_param_label.grid(column=2, row=0, sticky='w', padx=(6, 10), pady=0)

        self.separator_lower = ttk.Separator(self, orient=tk.HORIZONTAL)
        self.separator_lower.grid(column=0, row=4, columnspan=3, sticky='ew', padx=10, pady=(5, 0))

        # Parameter mapping controls
        self.parameters_frame = ttk.Frame(self)
        self.parameters_frame.grid(column=0, row=5, columnspan=3, sticky='nsew')
        for i in range(3):
            self.parameters_frame.columnconfigure(i)

        # Footer
        self.footer_frame = ttk.Frame(self)
        self.footer_frame.grid(column=0, columnspan=3, row=6,  sticky='ew')

        # Re-center button
        self.recenter_button = ttk.Button(self.footer_frame, text='Re-Center', width=20)
        self.recenter_button.grid(column=0, row=0, **self.options)

        # Musical scale settings
        self.scale_frame = ttk.Frame(self.footer_frame)
        self.scale_frame.grid(column=1, row=0,  sticky='ew', padx=3)
        self.scale_frame.columnconfigure(0, weight=1)
        self.scale_frame.columnconfigure(1, weight=2)
        self.scale_frame.columnconfigure(2, weight=1)
        self.scale_frame.columnconfigure(3, weight=2)

        self.root_label = ttk.Label(self.scale_frame, text='Root Note:')
        self.root_label.grid(column=0, row=0, **self.options)
        self.root_var_selector = ttk.Combobox(
            self.scale_frame,
            textvariable=self.active_root_name,
            values=self.note_names,
            width=4,
            state='readonly',
        )
        self.root_var_selector.grid(column=1, row=0, **self.options)

        self.scale_label = ttk.Label(self.scale_frame, text='Scale:')
        self.scale_label.grid(column=2, row=0, **self.options)

        self.scale_var_selector = ttk.Combobox(
            self.scale_frame,
            textvariable=self.active_scale,
            values=list(self.scale_patterns.keys()),
            width=14,
            state='readonly',
        )
        self.scale_var_selector.grid(column=3, row=0, **self.options)

        # Legato button
        self.legato_var = tk.BooleanVar(value=False, )
        self.legato_button = ttk.Button(
            self.footer_frame, 
            text='Legato', 
            style='Active.TButton' if self.legato_var.get() else 'Default.TButton',
            width=11,
            command=self._on_legato_button,
            state='disabled' # TODO: implement legato
        )
        self.legato_button.grid(column=2, row=0, **self.options)

    def _build_parameter_controls(self, index: int) -> None:
        """Builds input/output parameter mapping controls."""

        # Ensure the index key exists in patch data before reading
        str_index = str(index)
        param_data = self.settings.loaded_patch_parameters_data.get(
            str_index, 
            # default parameter values:
            {
                'input': None, 
                'input_range': [-1, 1], 
                'output': None, 
                'output_range': [0, 127],
                'mapping': False,
                'invert': False,
            } 
        )

        # Guards for missing values
        mapping_bool: bool = param_data.get('mapping', False)
        invert_bool: bool = param_data.get('invert', False)
        input_param: str | None = param_data.get('input', None)
        input_range: list = param_data.get('input_range') if len(param_data.get('input_range', [])) > 1 else [0, 100]
        output_param: str | None = param_data.get('output', None)
        output_range: list = param_data.get('output_range') if len(param_data.get('output_range', [])) > 1 else [0, 127]

        # Parameter mapping frame
        mapping_frame = ttk.Frame(self.parameters_frame)
        mapping_frame.grid(column=0, row=index, sticky='ew', padx=(2, 0))

        # Input parameter
        input_param_frame = ttk.Frame(mapping_frame)
        input_param_frame.grid(column=0, row=0, sticky='w', pady=5)

        input_param_var = tk.StringVar(value=input_param)
        input_param_selector = ttk.Combobox(
            input_param_frame,
            textvariable=input_param_var,
            values=[],
            width=6,
            state='readonly',
        )
        input_param_selector.grid(column=0, row=0, sticky='w', padx=10, pady=5)
        # Pass row index to callback
        input_param_selector.bind('<<ComboboxSelected>>', lambda e, i=index: self._on_type_selected(i))

        # Set input slider boundaries according to input sensor type
        if input_param == 'Speed':
            low_bound, high_bound = 0.0, 100.0
        else:
            low_bound, high_bound = -1.0, 1.0

        # Calculate current initial values as percentage steps [0, 100]
        span = high_bound - low_bound
        start_low = int(round(((input_range[0] - low_bound) / span) * 100))
        start_high = int(round(((input_range[1] - low_bound) / span) * 100))

        # Clamp initial steps to [0, 100]
        start_low = max(0, min(100, start_low))
        start_high = max(0, min(100, start_high))

        input_range_frame = ttk.Frame(input_param_frame)
        input_range_frame.grid(column=0, row=1, padx=(0, 0))
        
        # Display integer percentage steps [0, 100]
        input_range_label = ttk.Label(
            input_range_frame, 
            text=f'{start_low} : {start_high}'
        )
        input_range_label.grid(column=2, row=0)

        # Calculate current initial values as percentage steps [0, 100]
        span = high_bound - low_bound
        start_low = int(round(((input_range[0] - low_bound) / span) * 100))
        start_high = int(round(((input_range[1] - low_bound) / span) * 100))

        # Clamp initial steps to [0, 100]
        start_low = max(0, min(100, start_low))
        start_high = max(0, min(100, start_high))
            
        input_param_slider = RangeSlider(
            input_param_frame,
            from_=0,
            to=100,
            low=start_low,
            high=start_high,
            min_range=5,
            width=200,
            # Pass row index, low, and high values to callback
            command=lambda lo, hi, idx=index, lb=low_bound, hb=high_bound: 
                self._on_slider_change(idx, 'input_range', lo, hi, lb, hb)
        )
        input_param_slider.grid(column=1, row=1, sticky='w', padx=10, pady=5)

        # Connector
        connector_param_frame = ttk.Frame(mapping_frame)
        connector_param_frame.grid(column=1, row=0, sticky='w')

        connector_sep_l = ttk.Separator(connector_param_frame, orient=tk.VERTICAL)
        connector_sep_l.grid(column=0, row=0, rowspan=2, sticky='ns', padx=5, pady=20)

        connector_mapping_var = tk.BooleanVar(value=mapping_bool)
        connector_mapping_button = ttk.Button(
            connector_param_frame, 
            text='Exp.' if mapping_bool else 'Linear', 
            width=7,
            style='Active.TButton' if mapping_bool else 'Default.TButton',
            command=lambda idx=index: self._on_connector_mapping_button(idx,connector_mapping_var )
            )
        connector_mapping_button.grid(column=1, row=0, sticky='w', padx=5, pady=5)

        connector_invert_var = tk.BooleanVar(value=invert_bool)
        connector_invert_button = ttk.Button(
            connector_param_frame, 
            text='Invert', 
            width=4, 
            style='Active.TButton' if invert_bool else 'Default.TButton',
            command=lambda idx=index: self._on_connector_invert_button(idx, connector_invert_var)
            )
        connector_invert_button.grid(column=1, row=1, sticky='ew', padx=5, pady=(5, 7))

        connector_sep_r = ttk.Separator(connector_param_frame, orient=tk.VERTICAL)
        connector_sep_r.grid(column=2, row=0, rowspan=2, sticky='ns', padx=5, pady=20)

        # Output parameter
        output_param_frame = ttk.Frame(mapping_frame)
        output_param_frame.grid(column=2, row=0, sticky='w', pady=5)

        output_param_var = tk.StringVar(value=output_param)
        output_param_selector = ttk.Combobox(
            output_param_frame,
            textvariable=output_param_var,
            values=[],
            width=6,
            state='readonly',
        )
        output_param_selector.grid(column=0, row=0, sticky='w', padx=10, pady=5)
        # Pass row index to callback
        output_param_selector.bind('<<ComboboxSelected>>', lambda e, idx=index: self._on_type_selected(idx))

        output_range_frame = ttk.Frame(output_param_frame)
        output_range_frame.grid(column=0, row=1, padx=(0, 0))

        # Convert numbers to letter names for Note parameters
        if output_param == 'Note':
            quantized_low = snap_to_scale(output_range[0], self.settings.active_scale_full)
            quantized_high = snap_to_scale(output_range[1], self.settings.active_scale_full)
            signed_low = midi_to_signed_pitch(quantized_low)
            signed_high = midi_to_signed_pitch(quantized_high)
            output_range_text = f'{signed_low} : {signed_high}'
        else:
            output_range_text = f'{output_range[0]} : {output_range[1]}'

        output_range_label = ttk.Label(
            output_range_frame, 
            text=output_range_text
            )
        output_range_label.grid(column=0, row=0)

        output_param_slider = RangeSlider(
            output_param_frame,
            from_=0,
            to=127, # midi range
            low=output_range[0],
            high=output_range[1],
            width=200,
            min_range=5,
            # Pass row index, low, and high values to callback
            command=lambda lo, hi, idx=index: self._on_slider_change(idx, 'output_range', lo, hi)
        )
        output_param_slider.grid(column=1, row=1, sticky='w', padx=10, pady=5)

        # Separate parameter rows
        separator_under = ttk.Separator(mapping_frame, orient=tk.HORIZONTAL)
        separator_under.grid(column=0, row=1, columnspan=3, sticky='ew', padx=10, pady=0)

        # Keep references alive
        self.parameter_selector_widgets.append(((input_param_var, input_param_selector), (output_param_var, output_param_selector)))
        self.parameter_slider_widgets.append({
            'input_slider': input_param_slider,
            'input_label': input_range_label,
            'output_slider': output_param_slider,
            'output_label': output_range_label,
            'mapping_button': connector_mapping_button,
            'mapping_var': connector_mapping_var,
            'invert_button': connector_invert_button,
            'invert_var': connector_invert_var,
        })

        # Set initial slider state based on loaded values and update local patch data
        self._update_slider_states(index)
        self._sync_row_data(index)
        self._on_parameter_change()

    def _refresh_available_types(self) -> None:
        """Handles available parameter types across all rows so no type can be used more than once."""
        # Currently used output parameters
        output_selections = [
            out_var.get() for (in_var, in_sel), (out_var, out_sel) in self.parameter_selector_widgets
            if out_var.get()
        ]

        for (in_var, in_sel), (out_var, out_sel) in self.parameter_selector_widgets:
            # Input parameters can be used many times
            in_sel['values'] = [t for t in self.input_parameter_types]

            # Output parameters can only be used once
            own_output = out_var.get()
            available_output = [
                t for t in self.output_parameter_types
                if t not in output_selections or t == own_output
            ]
            out_sel['values'] = available_output

    def _sync_row_data(self, index: int):
        """Updates loaded patch data for a specific parameter widget row."""

        # Access parameter control widgets
        str_index = str(index)
        (in_var, _), (out_var, _) = self.parameter_selector_widgets[index]
        widgets = self.parameter_slider_widgets[index]
        in_slider = widgets['input_slider']
        out_slider = widgets['output_slider']

        # Check dictionary key entry exists
        if str_index not in self.settings.loaded_patch_parameters_data:
            self.settings.loaded_patch_parameters_data[str_index] = {}

        # Parameter selector variables
        input_param = in_var.get() or None
        output_param = out_var.get() or None

        # Determine sensor boundary range
        low_bound, high_bound = (0.0, 100.0) if input_param == 'Speed' else (-1.0, 1.0)
        span = high_bound - low_bound

        # Map input slider percentage [0..100] sensor bounds
        in_low_pct = in_slider.low_var.get()
        in_high_pct = in_slider.high_var.get()
        actual_in_low = round(low_bound + (in_low_pct / 100.0) * span, 2)
        actual_in_high = round(low_bound + (in_high_pct / 100.0) * span, 2)

        # Output MIDI range
        out_low = int(out_slider.low_var.get())
        out_high = int(out_slider.high_var.get())

        # Update patch parameter dictionary
        self.settings.loaded_patch_parameters_data[str_index] = {
            'input': input_param,
            'input_range': [actual_in_low, actual_in_high],
            'output': output_param,
            'output_range': [out_low, out_high],
            'mapping': widgets['mapping_var'].get(),
            'invert': widgets['invert_var'].get(),
        }

    def _on_type_selected(self, index: int) -> None:
        """Resets parameter and refreshes UI when parameter selection changes."""
        (in_var, _), (out_var, _) = self.parameter_selector_widgets[index]
        new_output = out_var.get() or None
        previous_output = self.active_output_tracker.get(index)

        # If output parameter changed or was set to empty, reset previous parameter
        if previous_output and previous_output != new_output:
            if hasattr(self.master.master, 'midi_player'):
                self.master.master.midi_player.reset_parameter(previous_output) #type: ignore

        # Update state tracker
        self.active_output_tracker[index] = new_output

        self._sync_row_data(index)
        self._refresh_available_types()
        self._update_slider_states(index)
        self._on_parameter_change()

    def _on_slider_change(self, 
                          index: int, 
                          range_key: str, 
                          low: float, 
                          high: float,
                          low_bound: float = 0.0,
                          high_bound: float = 127.0,
    ) -> None:
        """Called when a range slider changes."""
        str_index = str(index)
        if str_index not in self.settings.loaded_patch_parameters_data:
            self.settings.loaded_patch_parameters_data[str_index] = {}

        # Update the GUI Label corresponding to the modified slider
        widgets = self.parameter_slider_widgets[index]

        if range_key == 'input_range':
            # Map step integers [0, 100] back to target floats for underlying patch data
            actual_low = low_bound + (low / 100.0) * (high_bound - low_bound)
            actual_high = low_bound + (high / 100.0) * (high_bound - low_bound)

            # Display slider percentage steps directly
            widgets['input_label'].config(text=f'{int(low)} : {int(high)}')
            self.settings.loaded_patch_parameters_data[str_index][range_key] = [round(actual_low, 2), round(actual_high, 2)]

        elif range_key == 'output_range':
            # Output range is already MIDI [0, 127]
            actual_low = int(low)
            actual_high = int(high)

            # Convert numbers to letter names with numeric octave sign for Note parameters
            output_param = self.parameter_selector_widgets[index][1][0].get()
            if output_param == 'Note':
                # Quantize to active scale notes
                quantized_low = snap_to_scale(actual_low, self.settings.active_scale_full)
                quantized_high = snap_to_scale(actual_high, self.settings.active_scale_full)
                signed_low = midi_to_signed_pitch(quantized_low)
                signed_high = midi_to_signed_pitch(quantized_high)
                output_range_text = f'{signed_low} : {signed_high}'
            else:
                output_range_text = f'{actual_low} : {actual_high}'

            widgets['output_label'].config(text=output_range_text)
            self.settings.loaded_patch_parameters_data[str_index][range_key] = [actual_low, actual_high]

        self._on_parameter_change()

    def _update_parameter_list(self, *args) -> None:
        """Refreshes patch data, clears and rebuilds parameter controls."""
        loaded_patch = self.loaded_patch_name.get()
        cleaned_name = loaded_patch.removesuffix(' (default)')
        self.cleaned_loaded_patch_name.set(cleaned_name)    

        # Sync scale, root note and legato from saved patch data
        patch_info = self.settings.saved_patches_data.get('patches', {}).get(cleaned_name, {})
        if patch_info:
            if 'scale' in patch_info:
                self.active_scale.set(patch_info['scale'])
            if 'root_note' in patch_info:
                root_note = patch_info['root_note']
                self.active_root_name.set(self.note_names[root_note])
            if 'legato' in patch_info:
                self.legato_var.set(patch_info['legato'])
                self._update_legato_button()

        # Destroy all child widgets in parameters_frame 
        for child in self.parameters_frame.winfo_children():
            child.destroy()

        self.parameter_selector_widgets.clear()
        self.parameter_slider_widgets.clear()

        # self.settings.loaded_patch_parameters_data = self.settings.loaded_patch_parameters_data

        # Parameter controls
        for i in range(4):
            self._build_parameter_controls(i)

        # Populate dropdown values 
        self._refresh_available_types()
        self.patch_altered.set(False)
        
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
        """Updates active root note based on selected root name."""
        new_root_note = self.note_names.index(self.active_root_name.get())
        self.active_root_note.set(new_root_note)

    def _on_parameter_change(self, *args) -> None:
        """Flag parameter settings changes and update selector styles."""
        # Update style for all selector boxes
        for i in range(len(self.parameter_selector_widgets)):
            (in_var, in_sel), (out_var, out_sel) = self.parameter_selector_widgets[i]
            has_input = bool(in_var.get())
            has_output = bool(out_var.get())

            if has_input and has_output:
                in_sel.configure(style='Filled.TCombobox')
                out_sel.configure(style='Filled.TCombobox')
            elif has_input and not has_output:
                in_sel.configure(style='TCombobox')
                out_sel.configure(style='Empty.TCombobox')
            elif has_output and not has_input:
                in_sel.configure(style='Empty.TCombobox')
                out_sel.configure(style='TCombobox')
            else:
                in_sel.configure(style='TCombobox')
                out_sel.configure(style='TCombobox') 

        # Flag changes
        self.patch_altered.set(True)

    def _on_save_patch_button(self) -> None:
        """Saves current patch parameter configuration to Settings and settings.json."""
        patch_name = self.loaded_patch_name.get().removesuffix(' (default)')
        
        # Update active patch data inside Settings.saved_patches_data
        if patch_name in self.settings.saved_patches_data.get('patches', {}):
            patch_data = self.settings.saved_patches_data['patches'][patch_name]

            patch_data['parameters'] = self.settings.loaded_patch_parameters_data
            patch_data['channel'] = self.active_midi_channel.get()
            patch_data['root_note'] = self.active_root_note.get()
            patch_data['scale'] = self.active_scale.get()
            patch_data['legato'] = self.legato_var.get()
            
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

    def _update_channel_selector_state(self, *args) -> None:
        """Disables channel selector when running."""
        running = self.running_status.get()
        if running:
            self.channel_selector.config(state='disabled')
        else:
            self.channel_selector.config(state='normal')

    def _update_slider_states(self, index: int) -> None:
        """Disables and resets sliders if their corresponding combobox selector is empty."""
        (in_var, _), (out_var, _) = self.parameter_selector_widgets[index]
        widgets = self.parameter_slider_widgets[index]
        in_slider = widgets['input_slider']
        in_label = widgets['input_label']
        out_slider = widgets['output_slider']
        out_label = widgets['output_label']

        # Only enable mapping and invert buttons if both parameters set
        mapping_button = widgets['mapping_button']
        invert_button = widgets['invert_button']
        button_state = 'normal' if bool(in_var.get() and out_var.get()) else 'disabled'
        mapping_button.configure(state=button_state)
        invert_button.configure(state=button_state)

        # Disable input slider if input parameter is empty
        if not in_var.get():
            in_slider.configure(state='disabled')
            in_slider.set_range(in_slider.from_, in_slider.to)
            in_label.config(text=f'{int(in_slider.from_)} : {int(in_slider.to)}')
        else:
            in_slider.configure(state='normal')

        # Disable output slider if output parameter is empty
        if not out_var.get():
            out_slider.configure(state='disabled')
            out_slider.set_range(out_slider.from_, out_slider.to)
            out_label.config(text=f'{int(out_slider.from_)} : {int(out_slider.to)}')
        else:
            out_slider.configure(state='normal')

    def _on_connector_mapping_button(self, index: int, toggle_var: tk.BooleanVar) -> None:
        """Toggles the parameter mapping between linear and exponential."""
        widgets = self.parameter_slider_widgets[index]
        mapping_button = widgets['mapping_button']
        mapping_var = widgets['mapping_var']
        
        # Flip current toggle state
        new_state = not mapping_var.get()
        mapping_var.set(new_state)

        # Update visual button label
        if new_state:
            mapping_button.config(text='Exp.')
            mapping_button.config(style='Active.TButton')
        else:
            mapping_button.config(text='Linear')
            mapping_button.config(style='Default.TButton')

        # Flag patch changes and update parameter data
        self._sync_row_data(index)
        self._on_parameter_change()

    def _on_connector_invert_button(self, index: int, toggle_var: tk.BooleanVar) -> None:
        """Inverts the output parameter mapping range and updates patch state."""
        widgets = self.parameter_slider_widgets[index]
        invert_button = widgets['invert_button']
        invert_var = widgets['invert_var']

        # Flip current toggle state
        new_state = not invert_var.get()
        invert_var.set(new_state)

        # Update visual button label
        if new_state:
            invert_button.config(style='Active.TButton')
        else:
            invert_button.config(style='Default.TButton')

        # Flag patch changes and update parameter data
        self._sync_row_data(index)
        self._on_parameter_change()

    def _on_active_channel_changed(self, *args) -> None:
        """Syncs the UI MIDI channel (1-indexed) when active MIDI channel (0-indexed) changes."""
        actual_val = self.active_midi_channel.get()
        expected_display = actual_val + 1
        
        # Prevent trace loop
        if self.display_midi_channel.get() != expected_display:
            self.display_midi_channel.set(expected_display)

    def _on_display_channel_changed(self, *args) -> None:
        """Syncs the active MIDI channel on channel selector change."""
        try:
            display_val = self.display_midi_channel.get()
            # Clamp to valid [1, 16] range and convert to [0, 15]
            actual_val = max(0, min(127, display_val - 1))

            # Prevent trace loop
            if self.active_midi_channel.get() != actual_val:
                self.active_midi_channel.set(actual_val)

        except tk.TclError:
            # User typing
            pass

    def _on_recenter_button(self) -> None:
        """Flips recenter button state."""
        pass

    def _update_legato_button(self) -> None:
        """Refreshes legato button style."""
        new_state = self.legato_var.get()
        if new_state:
            self.legato_button.config(style='Active.TButton')
        else:
            self.legato_button.config(style='Default.TButton')

    def _on_legato_button(self) -> None:
        """Flips legato button state and updates style."""
        # Flip current toggle state
        new_state = not self.legato_var.get()
        self.legato_var.set(new_state)
        self.patch_altered.set(True)
        self._update_legato_button()


        