import numpy as np

def midi_map(
        value: float, input_range: list[float], midi_range: list[int]) -> int:
    """
    Maps linear data to discreet MIDI values with settable ranges
    Input values: input_range [2-value range], midi_range [2-value range within 0..127]
    """
    note = int(np.interp(value, input_range, midi_range))
    out = max(0, min(127, note)) # limit output to valid MIDI [0..127] range
    return out

