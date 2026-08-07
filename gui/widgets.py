import tkinter as tk

class RangeSlider(tk.Canvas):
    """A two-handle range slider."""

    def __init__(self, 
                 parent, 
                 from_=0, 
                 to=100, 
                 width=200, 
                 height=30,
                 low=None, 
                 high=None, 
                 min_range=10,
                 command=None, 
                 state='normal', 
                 **kwargs
    ):
        super().__init__(
            parent, 
            width=width, 
            height=height,
            highlightthickness=0, 
            **kwargs
        )

        self.from_ = from_
        self.to = to
        self.low = low
        self.high = high
        self.min_range = min_range # minimum distance to avoid handle overlap and sticking
        self.width = width
        self.height = height
        self.handle_radius = 8
        self.command = command  # callback: fn(low, high)
        self._state = state

        # Ensure initial values respect min_range
        init_low = low if low is not None else from_
        init_high = high if high is not None else to
        if init_high - init_low < self.min_range:
            init_high = min(init_low + self.min_range, to)
            init_low = max(init_high - self.min_range, from_)

        self.low_var = tk.DoubleVar(value=low if low is not None else from_)
        self.high_var = tk.DoubleVar(value=high if high is not None else to)

        self._active_handle = None  # 'low' or 'high' while dragging

        self.bind('<Button-1>', self._on_click)
        self.bind('<B1-Motion>', self._on_drag)
        self.bind('<Configure>', lambda e: self._redraw())

        self._redraw()

    def _value_to_x(self, value: float) -> float | int:
        """Value to pixel conversion."""
        span = self.to - self.from_
        frac = 0 if span == 0 else (value - self.from_) / span
        pad = self.handle_radius + 2
        return pad + frac * (self.width - 2 * pad)

    def _x_to_value(self, x: float) -> float | int:
        """Pixel to value conversion."""
        pad = self.handle_radius + 2
        frac = (x - pad) / (self.width - 2 * pad)
        frac = min(max(frac, 0), 1)
        return self.from_ + frac * (self.to - self.from_)

    def configure(self,cnf=None, **kw) -> None:
        """Override configure to intercept 'state' updates."""
        if cnf is None:
            cnf = {}
        if isinstance(cnf, dict):
            kw.update(cnf)

        if 'state' in kw:
            self._state = str(kw.pop('state')).lower()
            self._redraw()

        if kw:
            super().configure(**kw)

    def _redraw(self) -> None:
        self.delete('all')
        y = self.height // 2
        pad = self.handle_radius + 2

        # Color themes based on state
        is_disabled = self._state == 'disabled'
        track_bg = '#e0e0e0' if is_disabled else '#bbb'
        track_active = '#a0c4eb' if is_disabled else '#4a90d9'
        handle_fill = '#f5f5f5' if is_disabled else 'white'
        handle_outline = '#cccccc' if is_disabled else 'grey'

        # Track
        self.create_line(pad, y, self.width - pad, y, fill=track_bg, width=4, capstyle='round')

        low_x = self._value_to_x(self.low_var.get())
        high_x = self._value_to_x(self.high_var.get())

        # Selected range highlight
        self.create_line(low_x, y, high_x, y, fill=track_active, width=4, capstyle='round')

        # Handles
        r = self.handle_radius
        self.create_oval(low_x - r, y - r, low_x + r, y + r,
                          fill=handle_fill, outline=handle_outline, width=2, tags='low_handle')
        self.create_oval(high_x - r, y - r, high_x + r, y + r,
                          fill=handle_fill, outline=handle_outline, width=2, tags='high_handle')

    def _on_click(self, event) -> None:
        # Ignore clicks when disabled
        if self._state == 'disabled':
            return  
            
        low_x = self._value_to_x(self.low_var.get())
        high_x = self._value_to_x(self.high_var.get())

        # Pick whichever handle is closer to the click
        if abs(event.x - low_x) <= abs(event.x - high_x):
            self._active_handle = 'low'
        else:
            self._active_handle = 'high'
        self._on_drag(event)

    def _on_drag(self, event) -> None:
        # Ignore drags when disabled
        if self._state == 'disabled':
            return
        
        """Enforces minimum range while dragging."""
        value = self._x_to_value(event.x)

        if self._active_handle == 'low':
            max_allowed = self.high_var.get() - self.min_range # clamp low handle
            value = min(value, max_allowed)
            self.low_var.set(value)
        elif self._active_handle == 'high':
            min_allowed = self.low_var.get() + self.min_range # clamp high handle
            value = max(value, min_allowed)
            self.high_var.set(value)

        self._redraw()
        if self.command:
            self.command(self.low_var.get(), self.high_var.get())

    def get_range(self) -> tuple[float, float]:
        """Returns slider range."""
        return self.low_var.get(), self.high_var.get()

    def set_range(self, low: int, high: int) -> None:
        """Sets range, conforming to minimum range."""
        low = max(low, self.from_)
        high = min(high, self.to)

        if high - low < self.min_range:
            high = min(low + self.min_range, self.to)
            low = max(high - self.min_range, self.from_)

        self.low_var.set(low)
        self.high_var.set(high)
        self._redraw()
