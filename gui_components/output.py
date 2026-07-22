import tkinter as tk
from tkinter import ttk
import mido as md # type supressions needed for Backend methods

class MidiFrame(ttk.Frame):
    """ GUI container for MIDI config controls. """

    def __init__(self, container, settings):
        super().__init__(container)
        self.name = 'MIDI Settings'
        self.settings = settings
        self.options = {'sticky': 'w', 'padx':10, 'pady':(10, 5)} # widgit placement options
        self.default_outport_name = settings.default_outport
        self.midi_outports = []
        self.selected_outport = None
        self.connection_state = False # connection state flag
        self.connected_outport = None
        self.connected_outport_name = None

        # Configure columns
        for i in range(2):
            self.columnconfigure(i, weight=1)

        self._create_widgets()
        self._refresh_outports_list()
            
    def _create_widgets(self):
        # Available MIDI outports list
        self.outports_label = ttk.Label(self, text='Available MIDI Output Ports:')
        self.outports_label.grid(column=0, row=0, **self.options)

        self.refresh_button = ttk.Button(self, text='Refresh', command=self._refresh_outports_list)
        self.refresh_button.grid(column=1, row=0, sticky='e', padx=10, pady=(10, 5))

        self.outports_list = ttk.Treeview(self, columns=('port','status', 'default'), show='headings', height=8, selectmode='browse')
        self.outports_list.heading('port', text='Port Name')
        self.outports_list.column('port', width=200, anchor='w')
        self.outports_list.heading('status', text='Connection Status')
        self.outports_list.column('status', width=60, anchor='w')
        self.outports_list.heading('default', text='Default Port')
        self.outports_list.column('default', width=40, anchor='w')
        self.outports_list.grid(column=0, row=2, columnspan=2, padx=10, pady=(0, 10), sticky='nsew')
        self.outports_list.bind('<<TreeviewSelect>>', self._on_outport_select)

        # List item colour tags
        self.outports_list.tag_configure('unconnected', foreground='blue')
        self.outports_list.tag_configure('connected', foreground='green')
        self.outports_list.tag_configure('unavailable', foreground='red')
        
        # Connection buttons
        self.connect_button = ttk.Button(self, text='Connect', state='disabled', command=self._connect_outport)
        self.connect_button.grid(column=0, row=3, padx=10, pady=10, sticky='w')
        self.set_default_button = ttk.Button(self, text='Set as Default Port', state='disabled', command=self._on_set_default)
        self.set_default_button.grid(column=1, row=3, padx=10, pady=10, sticky='w')

    def _update_connection_button_states(self):
        """ Updates connection and default button states based on selection and connection. """
        # Connection button logic
        if self.connection_state:
            self.connect_button.config(state='normal')
        elif self.selected_outport:
            self.connect_button.config(state='normal')
        else:
            self.connect_button.config(state='disabled')
        # Set default button logic
        if self.selected_outport and self.selected_outport != self.default_outport_name:
            self.set_default_button.config(state='normal')
        else:
            self.set_default_button.config(state='disabled')

    def _set_status(self, state: bool):
        """ Sets connection status label and button states. """
        # Set connection status
        if not isinstance(state, bool):
            raise ValueError('Connection status must be a bool')
        # Set refresh and connection button states
        connection = self.connection_state = state
        if connection:
            self.refresh_button.config(state='disabled')
            self.connect_button.config(text='Disconnect', command=self._disconnect_outport)
            self.outports_list.config(selectmode='none')
            self._update_connection_button_states()
        else:
            self.refresh_button.config(state='normal')
            self.connect_button.config(text='Connect', command=self._connect_outport)
            self.outports_list.config(selectmode='browse')
            self._update_connection_button_states()
    
    def _on_outport_select(self, event):
        """ Captures selected output port name. """
        selected_items = self.outports_list.selection()
        if not selected_items:
            self.selected_outport = None
            self._update_connection_button_states()
            return

        selected_item = selected_items[0]
        tags = self.outports_list.item(selected_item, 'tags')
        if 'unavailable' in tags:
            self.outports_list.selection_remove(selected_item)
            self.selected_outport = None
            self._update_connection_button_states()
            return

        values = self.outports_list.item(selected_item, 'values')
        port_name = values[0] if values else None
        self.selected_outport = None if port_name == None else port_name
        self._update_connection_button_states()

    def _on_set_default(self):
        """ Makes the selected ouput port the new default port. """
        self.default_outport_name = self.selected_outport
        self._refresh_outports_list()
        # TODO: update default port in global settings

    def _connect_outport(self):
        """ Opens connection with selected MIDI output port. """
        self.connected_outport_name = self.selected_outport
        self.connected_outport = md.open_output(self.connected_outport_name) # type: ignore
        self._set_status(True)
        self._refresh_outports_list()
        print(f'{self.connected_outport} opened')
        
    def _disconnect_outport(self):
        """ Resets then closes active MIDI output port. """
        port = self.connected_outport
        if port:
            port.reset() # type: ignore # all notes off and reset all controllers
            port.close() # type: ignore
            print(f'{self.connected_outport} closed')
            self.connected_outport = None
            self.connected_outport_name = None
            self._set_status(False)
            self._refresh_outports_list()

    def _focus_list(self):
            """ Focuses selection on the connected or default item if present. """
            focus_name = None
            focus_item = None
            # Prioritise connection over default
            if self.connection_state:
                focus_name = self.connected_outport_name
                print(f'connected: {focus_name}')
            elif self.default_outport_name:
                focus_name = self.default_outport_name
                print(f'default: {focus_name}')
            # Match port name to list item
            for item in self.outports_list.get_children():
                values = self.outports_list.item(item, 'values')
                if values and values[0] == focus_name:
                    focus_item = item
                    break
            # Focus list item, update selection and button states
            if focus_item:
                self.outports_list.selection_set(focus_item)
                self.outports_list.focus(focus_item)
                self.outports_list.see(focus_item)
                self.selected_outport = self.default_outport_name
                self._update_connection_button_states()

    def _refresh_outports_list(self):
        """ Clears outports list and rescans for available MIDI output ports. """
        # Delete all list children
        for item in self.outports_list.get_children():
            self.outports_list.delete(item)
        # Scan for available ports
        self.midi_outports = md.get_output_names() # type: ignore
        if not self.midi_outports:
            self.midi_outports = []
        # Add available ports to list with default connection status
        for connection in self.midi_outports:
            default_status = ''
            if connection == self.default_outport_name:
                default_status = 'Default'
            if connection == self.connected_outport_name:
                self.outports_list.insert('', tk.END, values=(connection, 'Connected', default_status), tags=('connected',))
            else:
                self.outports_list.insert('', tk.END, values=(connection, 'Unconnected', default_status), tags=('unconnected'))
        # If default port unavailable, flag in list
        if self.default_outport_name not in self.midi_outports:
            self.outports_list.insert('', tk.END, values=(self.default_outport_name, 'Unavailable', 'Default'), tags=('unavailable'))

        self._focus_list()

    


