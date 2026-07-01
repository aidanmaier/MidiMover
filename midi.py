import mido
import time

class MidiOut():
    def __init__(self, portName: str, chan: int) -> None:
        """
        Configures MIDI connection at given port and channel
        Input values: portName [any valid string], channel [0..15]
        """
        self.port_name = portName
        self.channel = chan
        self._outport = mido.open_output(self.port_name)  # type: ignore

        # Default MIDI CC controls
        self.controls = {
            'mod': 1,
            'volume': 7,
            'resonance': 71,
            'release': 72,
            'attack': 73,
            'cutoff': 74,
            'portamento': 84,
            'reverb': 91,
            'tremolo': 92,
            'chorus': 93,
            'phaser': 95,
        }

    def close(self) -> None:
        self._outport.close()
    
    def note(self, pitch: int, vel: int, dur: float = 0) -> None:
        """
        Midi Note On message with auto Note Off message after waiting duration
        Input values: pitch (semitones) [0..127], vel [0..127], dur (seconds) [any float]
        """
        port = self._outport
        chan = self.channel
        note_on = mido.Message('note_on', channel=chan, note=pitch, velocity=vel)
        note_off = mido.Message('note_off', channel=chan, note=pitch, velocity=64)
        port.send(note_on)
        time.sleep(dur)
        port.send(note_off)
    
    def cc(self, ctrl: int, val: int) -> None:
        """
        MIDI Control Change message
        Input values: ctrl [0..127], val [0..127]
        """
        port = self._outport
        chan = self.channel
        cc = mido.Message('control_change', channel=chan, control=ctrl, value=val )
        port.send(cc)