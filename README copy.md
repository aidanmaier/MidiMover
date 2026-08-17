Zero-config WebSockets connection client for accessing Android IMU data

Code adapted from original by UmerCodez:

[https://github.com/UmerCodez/SensorServer/wiki/Connecting-To-the-Server-Using-Service-Discovery]


WebSockets server initialised using **Sensor Server** by UmerCodez

GitHub [https://github.com/UmerCodez/SensorServer]

F-Droid [https://f-droid.org/packages/github.umer0586.sensorserver/]



Guide to connecting a DAW to a virtual MIDI bus on MAC or Windows OS
[https://help.ableton.com/hc/en-us/articles/209774225-Setting-up-a-virtual-MIDI-bus]

Recommended quick output test set-up using BandLab (free, browser-based DAW):
1. For Windows users - install and start loopMIDI [https://www.tobias-erichsen.de/software/loopmidi.html].
2. Set up MidiMover using IAC Driver (MAC) or loopMIDI (Windows) as your MIDI output (Connections tab).
3. Open BandLab online studio [https://help.bandlab.com/hc/en-us/articles/115002945153-Getting-Started-with-the-BandLab-Studio]
4. Allow BandLab access to your MIDI devices (pop-up).
5. Load a virtual instrument in the BandLab studio (recommended: Percussion > Marimba).
6. Set IAC Driver/loopMIDI as your MIDI device in BandLab [https://help.bandlab.com/hc/en-us/articles/58150962949785-Connecting-MIDI-Devices].
7. Try playing the virtual keyboard inside GarageBand to check your audio connection [https://help.bandlab.com/hc/en-us/articles/56922726115097-Audio-Output-Issues].
8. Start MidiMover and try moving the controller to control the audio output.

Please Note:
- BandLab will not automatically sync all MIDI controls, but MIDI notes and Volume have worked in testing.
- Latency may be more noticable using a browser-based DAW than a local one.


**License GPL-3.0**