import numpy as np

# octave patterns for a selection of common (12-tet) scales 
scale_patterns = {
    'chromatic': [i for i in range(11)],
    'whole_tone': [i for i in range(0, 11, 2)],
    'octatonic': [0, 2, 3, 5, 6, 8, 9, 11],
    'major': [0, 2, 4, 5, 7, 9, 11],
    'lydian': [0, 2, 4, 6, 7, 9, 11],
    'mixolydian': [0, 2, 4, 5, 7, 9, 10],
    'mel_minor': [0, 2, 3, 5, 7, 9, 11],
    'dorian': [0, 2, 3, 5, 7, 9, 10],
    'nat_minor': [0, 2, 3, 5, 7, 8, 10],
    'phrygian': [0, 1, 3, 5, 7, 8, 10],
    'harm_minor': [0, 2, 3, 5, 7, 8, 11],
    'maj_pentatonic': [0, 2, 4, 7, 9],
    'min_pentatonic': [0, 3, 5, 7, 10],
    # 'pelog': [],
    # 'sorog': [],
}

class Scale():
    def __init__(self, root: int, type: str) -> None:
        """
        Holds MIDI note values for a given scale type and root note
        Input values:
            root [0..11],
            type [valid scale types held in mapping.scale_patterns]
        """
        self.root = root
        self.type = type
        self.pattern = scale_patterns[type] # degrees of the chromatic scale (1 octave)
        self.steps = len(self.pattern) # number of degrees per octave

        # transpose scale to start on root and order by asc = lowest octave of scale
        self.octave = sorted([(note + root) % 12 for note in self.pattern])
        
        # all scale notes falling within MIDI [0..127] range
        full_scale = [note for note in self.octave]
        for octave in range(1, 11):
            for note in self.octave:
                new_note = note + (12 * octave)
                if new_note < 128:
                    full_scale.append(new_note)
        self.full = full_scale

def midi_map(value: float, input_range: list[float], midi_range: list[int] = [0, 127]) -> int:
    """
    Maps linear data to discreet MIDI note values with settable input and output ranges
    Default output range is full MIDI note range [0..127]
    Input values: 
        input_range [2-value range], 
        midi_range [2-value range within 0..127]
    """
    note = int(np.interp(value, input_range, midi_range))
    out = max(0, min(127, note)) # limit output to valid MIDI [0..127] range
    return out

def pitchwheel_map(value: float, input_range: list[float], pitchwheel_range: list[int] = [-8192, 8191]) -> int:
    """
    Maps linear data to discreet MIDI pitchwheel values with settable input and output ranges
    Default output range is full MIDI pitchwheel range [-8192..8191]
    Input values: 
        input_range [floor, ceiling], 
        pitchweel_range [[floor, ceiling] within -8192..8191]
    """
    mod = int(np.interp(value, input_range, pitchwheel_range))
    out = max(-8192, min(8191, mod)) # limit output to valid pitchwheel [-8192..8191] range
    return out