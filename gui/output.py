import tkinter as tk
from tkinter import ttk
import mido as md # type supressions needed for Backend methods

class MidiFrame(ttk.Frame):
    """ GUI container for configuring MIDI output connections. """

    def __init__(self, container, settings):
        super().__init__(container)
        self.name = 'MIDI Settings'
        self.settings = settings
        self.options = {'sticky': 'w', 'padx':10, 'pady':(10, 5)} # widgit placement options
        self.refresh_interval = 2000 # poll rate for finding available devices (ms)

        self.default_outport_name = settings.default_outport.get()
        self.available_outports = []
        self.selected_outport_name = None
        self.connection_state = False # connection state flag
        self.connected_outport = None
        self.connected_outport_name = None

        # Configure columns
        for i in range(2):
            self.columnconfigure(i, weight=10)
        self.columnconfigure(2, weight=1)

        self._create_widgets()
        self.bind('<Destroy>', self._on_destroy)
        self._refresh_outports_list()
        
            
    def _create_widgets(self):
        # Available MIDI outports list
        self.outports_label = ttk.Label(self, text='Available MIDI Output Ports:')
        self.outports_label.grid(column=0, row=0, **self.options)

        self.refresh_button = ttk.Button(self, text='Refresh', command=self._refresh_outports_list)
        self.refresh_button.grid(column=1, row=0, sticky='e', padx=0, pady=(10, 5))

        self.outports_list = ttk.Treeview(self, columns=('port','status', 'default'), show='headings', height=6, selectmode='browse')
        self.outports_list.heading('port', text='Port Name')
        self.outports_list.column('port', width=200, anchor='w')
        self.outports_list.heading('status', text='Connection Status')
        self.outports_list.column('status', width=60, anchor='w')
        self.outports_list.heading('default', text='Default Port')
        self.outports_list.column('default', width=40, anchor='w')
        self.outports_list.grid(column=0, row=2, columnspan=2, padx=(10, 0), pady=0, sticky='nsew')
        self.outports_list.bind('<<TreeviewSelect>>', self._on_outport_select)

        # Scrollbar linked to outports list
        self.outports_scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.outports_list.yview)
        self.outports_scrollbar.grid(column=2, row=2, padx=0, pady=0, sticky='ns')
        self.outports_list.config(yscrollcommand=self.outports_scrollbar.set)

        # List item colour tags
        self.outports_list.tag_configure('unconnected', foreground='blue')
        self.outports_list.tag_configure('connected', foreground='green')
        self.outports_list.tag_configure('unavailable', foreground='red')
        
        # Connection buttons
        self.connect_button = ttk.Button(self, text='Connect', state='disabled', command=self._connect_outport)
        self.connect_button.grid(column=0, row=3, **self.options)
        self.set_default_button = ttk.Button(self, text='Set as Default Port', state='disabled', command=self._on_set_default)
        self.set_default_button.grid(column=1, row=3, sticky='e', padx=0, pady=(10, 5))

    def _update_connection_button_states(self):
        """ Updates connection and default button states based on selection and connection. """
        # Connection button logic
        if self.connection_state:
            self.connect_button.config(state='normal')
        elif self.selected_outport_name:
            self.connect_button.config(state='normal')
        else:
            self.connect_button.config(state='disabled')

        # Set Default button logic
        if self.selected_outport_name and self.selected_outport_name != self.default_outport_name:
            self.set_default_button.config(state='normal')
        else:
            self.set_default_button.config(state='disabled')

    def _set_status(self, state: bool):
        """ Sets connection status label and button states. """
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
            self.connected_outport = None
            self.connected_outport_name = None
            self._update_connection_button_states()
            
    
    def _on_outport_select(self, event=None):
        """ Captures selected output port name. """
        selected_items = self.outports_list.selection()
        if not selected_items:
            self.selected_outport_name = None
            self._update_connection_button_states()
            return

        selected_item = selected_items[0]
        tags = self.outports_list.item(selected_item, 'tags')
        if 'unavailable' in tags:
            self.outports_list.selection_remove(selected_item)
            self.selected_outport_name = None
            self._update_connection_button_states()
            return

        values = self.outports_list.item(selected_item, 'values')
        port_name = values[0] if values else None
        self.selected_outport_name = None if port_name == None else port_name
        self._update_connection_button_states()

    def _on_set_default(self):
        """ Makes the selected MIDI output port the new default port. """
        if not self.selected_outport_name:
            return
        
        self.default_outport_name = self.selected_outport_name # update local setting
        self.settings.default_outport.set(self.selected_outport_name) # update global setting
        self._refresh_outports_list()

    def _connect_outport(self):
        """ Opens connection with selected MIDI output port. """
        self.connected_outport_name = self.selected_outport_name
        self.connected_outport = md.open_output(self.connected_outport_name) # type: ignore
        self._set_status(True) # update local setting
        self.settings.output_connection.set(self.selected_outport_name) # update global setting
        self.settings.output_connection_status.set(True)
        self._refresh_outports_list()
        print(self.connected_outport) # DEBUG
        
    def _disconnect_outport(self):
        """ Resets then closes active MIDI output port. """
        port = self.connected_outport
        if port:
            port.reset() # type: ignore # all notes off and reset all controllers
            port.close() # type: ignore
            print(self.connected_outport) # DEBUG
            self._set_status(False) # update local setting
            self.settings.output_connection.set('< Connect MIDI Port >') # update global setting
            self.settings.output_connection_status.set(False)
            self._refresh_outports_list()

    def _kill_outport(self):
        """ Immediately resets active MIDI output port. """
        port = self.connected_outport
        if port:
            port.panic() # type: ignore # abruptly end all sounding notes
            port.close() # type: ignore
            print(self.connected_outport)
            self._set_status(False)
            self._refresh_outports_list()

    def _focus_list(self):
            """ Focuses selection on the connected or default item if present. """
            focus_name = None
            focus_item = None
            # Priority: connected -> selected -> default
            if self.connection_state:
                focus_name = self.connected_outport_name
            elif self.selected_outport_name:
                focus_name = self.selected_outport_name
            elif self.default_outport_name:
                focus_name = self.default_outport_name
            # Update global settings
            if focus_name == None:
                self.settings.output_connection.set('< Connect MIDI Port >')
            else:
                self.settings.output_connection.set(focus_name)
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
                self.selected_outport_name = self.default_outport_name
                self._update_connection_button_states()
                

    def _refresh_outports_list(self):
        """ Clears outports list and rescans for available MIDI output ports. """
        # Delete all list children
        for item in self.outports_list.get_children():
            self.outports_list.delete(item)

        # Scan for available ports
        self.available_outports = md.get_output_names() # type: ignore
        if not self.available_outports:
            self.available_outports = []

        # Add available ports to list with default connection status
        for connection in self.available_outports:
            default_status = ''
            if connection == self.default_outport_name:
                default_status = 'Default'
            if connection == self.connected_outport_name:
                self.outports_list.insert('', tk.END, values=(connection, 'Connected', default_status), tags=('connected',))
            else:
                self.outports_list.insert('', tk.END, values=(connection, 'Available', default_status), tags=('unconnected',))

        # If default port unavailable, flag in list
        if self.default_outport_name and self.default_outport_name not in self.available_outports:
            self.outports_list.insert('', tk.END, values=(self.default_outport_name, 'Unavailable', 'Default'), tags=('unavailable',))

        # Focus on connected or default item
        self._focus_list()

        # Call self after refresh interval
        self._refresh_job = self.after(self.refresh_interval, self._refresh_outports_list)

    def _on_destroy(self, event):
        """ Cleanup handler, closes Zeroconf before closing. """
        if event.widget is not self:
            return
        
        # if self._refresh_job is not None:
        #     self.after_cancel(self._refresh_job)
        #     self._refresh_job = None
        # self.zeroconf.close()


