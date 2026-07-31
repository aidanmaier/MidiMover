import tkinter as tk

class RangeSlider(tk.Canvas):
    """A two-handle range slider built on Canvas."""

    def __init__(self, parent, from_=0, to=100, width=200, height=30,
                 low=None, high=None, command=None, **kwargs):
        super().__init__(parent, width=width, height=height,
                          highlightthickness=0, **kwargs)

        self.from_ = from_
        self.to = to
        self.width = width
        self.height = height
        self.handle_radius = 8
        self.command = command  # callback: fn(low, high)

        self.low_var = tk.DoubleVar(value=low if low is not None else from_)
        self.high_var = tk.DoubleVar(value=high if high is not None else to)

        self._active_handle = None  # 'low' or 'high' while dragging

        self.bind('<Button-1>', self._on_click)
        self.bind('<B1-Motion>', self._on_drag)
        self.bind('<Configure>', lambda e: self._redraw())

        self._redraw()

    # -- value <-> pixel conversion --
    def _value_to_x(self, value):
        span = self.to - self.from_
        frac = 0 if span == 0 else (value - self.from_) / span
        pad = self.handle_radius + 2
        return pad + frac * (self.width - 2 * pad)

    def _x_to_value(self, x):
        pad = self.handle_radius + 2
        frac = (x - pad) / (self.width - 2 * pad)
        frac = min(max(frac, 0), 1)
        return self.from_ + frac * (self.to - self.from_)

    def _redraw(self):
        self.delete('all')
        y = self.height // 2
        pad = self.handle_radius + 2

        # Track
        self.create_line(pad, y, self.width - pad, y, fill='#bbb', width=4, capstyle='round')

        low_x = self._value_to_x(self.low_var.get())
        high_x = self._value_to_x(self.high_var.get())

        # Selected range highlight
        self.create_line(low_x, y, high_x, y, fill='#4a90d9', width=4, capstyle='round')

        # Handles
        r = self.handle_radius
        self.create_oval(low_x - r, y - r, low_x + r, y + r,
                          fill='white', outline='#4a90d9', width=2, tags='low_handle')
        self.create_oval(high_x - r, y - r, high_x + r, y + r,
                          fill='white', outline='#4a90d9', width=2, tags='high_handle')

    def _on_click(self, event):
        low_x = self._value_to_x(self.low_var.get())
        high_x = self._value_to_x(self.high_var.get())
        # Pick whichever handle is closer to the click
        if abs(event.x - low_x) <= abs(event.x - high_x):
            self._active_handle = 'low'
        else:
            self._active_handle = 'high'
        self._on_drag(event)

    def _on_drag(self, event):
        value = self._x_to_value(event.x)
        if self._active_handle == 'low':
            value = min(value, self.high_var.get())
            self.low_var.set(value)
        elif self._active_handle == 'high':
            value = max(value, self.low_var.get())
            self.high_var.set(value)
        self._redraw()
        if self.command:
            self.command(self.low_var.get(), self.high_var.get())

    def get_range(self):
        return self.low_var.get(), self.high_var.get()

    def set_range(self, low, high):
        self.low_var.set(low)
        self.high_var.set(high)
        self._redraw()