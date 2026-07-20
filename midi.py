import mido
import asyncio

# Default MIDI CC controls
control_codes = {
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

class MidiOut():
    def __init__(self, portName: str, channel: int) -> None:
        """
        Wrapper for Mido output functionality
        Auto-configures a MIDI output at the given port and channel
        Input values: 
            portName [any valid string], 
            channel [0..15]
        """
        self.port_name = portName
        self.channel = channel
        self._outport = mido.open_output(self.port_name)  # type: ignore

    def close(self) -> None:
        """
        Closes the output port
        """
        self._outport.close()
    
    def noteOn(self, pitch: int) -> None:
        """
        Starts a sustained note at the given pitch with velocity=64
        Input values: pitch [0..127]
        """
        msg = mido.Message('note_on', channel=self.channel, note=pitch, velocity=64)
        self._outport.send(msg)

    def noteOff(self, pitch: int) -> None:
        """
        Ends the note at the given pitch
        Input values: pitch [0..127]
        """
        msg = mido.Message('note_off', channel=self.channel, note=pitch, velocity=0)
        self._outport.send(msg)
        
    def pitchMod(self, mod: int, ) -> None:
        """
        Continuous pitch modification via pitchwheel message
        Input values: mod [-8192..8191]
        """
        msg = mido.Message('pitchwheel', channel=self.channel, pitch=mod)
        self._outport.send(msg)

    async def perc(self, pitch: int, duration: float = 0.1) -> None:
        """
        Play asyncronous time-limited note at the given pitch
        MIDI Note On message with auto Note Off message after awaiting duration
        Input values: 
            pitch (semitones) [0..127], 
            velocity [0..127], 
            duration (seconds) [any float]
        """
        self.noteOn(pitch=pitch)
        await asyncio.sleep(duration)
        self.noteOff(pitch=pitch)
    
    def cc(self, control: str, value: int) -> None:
        """
        MIDI Control Change message
        Input values: 
            control [valid controls held in midi.control_codes], 
            value [0..127]
        """
        outport = self._outport
        channel = self.channel
        control_code = control_codes[control]
        cc = mido.Message('control_change', channel=channel, control=control_code, value=value )
        outport.send(cc)