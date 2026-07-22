import tkinter as tk
from tkinter import ttk
import asyncio
import threading
from capture import DataStreamer

class ConnectionFrame(ttk.Frame):
    """ Frame for configuring input device connections. """
    
    def __init__(self, container, settings):
        super().__init__(container)
        self.name = 'Connect Device'
        self.settings = settings
        self.options = {'sticky': 'w', 'padx':10, 'pady':(10, 5)}

        self.status_var = tk.StringVar(value='Unconnected') # connection status label
        self.stream_thread = None
        self.stream_running = False
        self.stop_event = None
        self.active_connections = ['No active connections']

        # Configure columns
        for i in range(2):
            self.columnconfigure(i, weight=1)

        self._create_widgets()
        self._refresh_connections()

    def _create_widgets(self):
        # Connection status (row 0)
        ttk.Label(self, text='Connection status:').grid(column=0, row=0, **self.options)
        ttk.Label(self, textvariable=self.status_var, foreground='blue').grid(column=1, row=0, **self.options)

        # Connect/disconnect buttons (row 1)
        self.connect_button = ttk.Button(self, text='Connect', command=self._start_stream)
        self.connect_button.grid(column=0, row=1, padx=10, pady=10, sticky='w')
        self.disconnect_button = ttk.Button(self, text='Disconnect', command=self._stop_stream, state='disabled')
        self.disconnect_button.grid(column=1, row=1, padx=10, pady=10, sticky='w')

        # Active connections (rows 2-3)
        ttk.Label(self, text='Active connections:').grid(column=0, row=2, columnspan=2, **self.options)
        self.connections_list = ttk.Treeview(self, columns=('device',), show='headings', height=8)
        self.connections_list.heading('device', text='Device')
        self.connections_list.column('device', width=250, anchor='w')
        self.connections_list.grid(column=0, row=3, columnspan=2, padx=10, pady=(0, 10), sticky='nsew')

    def _set_status(self, message):
        """ Set connection status label. """
        self.status_var.set(message)

    def _update_buttons(self):
        if self.stream_running:
            self.connect_button.configure(state='disabled')
            self.disconnect_button.configure(state='normal')
        else:
            self.connect_button.configure(state='normal')
            self.disconnect_button.configure(state='disabled')

    def _refresh_connections(self):
        for item in self.connections_list.get_children():
            self.connections_list.delete(item)

        if not self.active_connections:
            self.active_connections = ['No active connections']

        for connection in self.active_connections:
            self.connections_list.insert('', tk.END, values=(connection,))

    def _start_stream(self):
        if self.stream_running:
            return
        else:
            self.stream_running = True
            self.stop_event = threading.Event()
            self._update_buttons()
            self._set_status('Connecting...')
            self.active_connections = ['Connect input device ...']
            self._refresh_connections()

            self.stream_thread = threading.Thread(target=self._run_stream, daemon=True)
            self.stream_thread.start()

    def _run_stream(self):
        data = DataStreamer(
            self.settings.ws_address, 
            self.settings.sensors
                            )

        def handle_sample(sample):
            service_name = sample.get('service_name')
            service_address = sample.get('address')
            service_port = sample.get('port')
            self.active_connections = [f"Device: {service_name} {service_address}:{service_port}"]
            self.after(0, self._refresh_connections)

        async def run_stream():
            await data.stream(
                handle_sample, 
                self.settings.sample_rate, 
                # wait_for_user=False,
                # stop_event=self.stop_event
                              )

        try:
            asyncio.run(run_stream())
            self.after(0, lambda: self._set_status('Stream finished'))
        except Exception as exc:
            self.after(0, lambda: self._set_status(f'Error: {exc}'))
        finally:
            self.after(0, self._finish_stream)

    def _finish_stream(self):
        self.stream_running = False
        self.active_connections = ['No active connections']
        self._refresh_connections()
        self._update_buttons()
        self._set_status('Disconnected')

    def _stop_stream(self):
        if self.stop_event is not None:
            self.stop_event.set()
        self._set_status('Stopping...')
        self.stream_running = False
        self.active_connections = ['No active connections']
        self._refresh_connections()
        self._update_buttons()